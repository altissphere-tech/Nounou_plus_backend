"""
Modèle User personnalisé pour NOUNOU+.

Pourquoi personnaliser ? Django utilise l'email ou un nom d'utilisateur par défaut.
Ici, l'identifiant unique est le numéro de téléphone (adapté au contexte RDC).

Moyens de connexion (choix du fondateur) :
- numéro de téléphone + code SMS (toujours possible) ;
- e-mail + mot de passe (facultatif, avec « mot de passe oublié ») ;
- compte Google ou Apple (voir SocialAccount et social.py).
Le numéro de téléphone reste obligatoire pour tous : c'est la coordonnée
montrée à l'autre personne après un match mutuel.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)


class OTPUnavailableError(Exception):
    """Levée quand aucun moyen d'envoyer un OTP n'est configuré (ex : en production en V1)."""


class UserManager(BaseUserManager):
    """Gestionnaire du modèle User — remplace le manager par défaut de Django."""

    def create_user(self, phone, role, password=None, **extra_fields):
        if not phone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        if role not in [User.ROLE_CLIENT, User.ROLE_WORKER, User.ROLE_ADMIN]:
            raise ValueError(f"Rôle invalide : {role}")
        user = self.model(phone=phone, role=role, **extra_fields)
        # Sans mot de passe, la connexion se fait par code SMS (ou Google / Apple) :
        # on fixe alors un mot de passe inutilisable pour respecter le contrat Django.
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """Crée un admin Django (accès à l'interface /admin/)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        user = self.model(phone=phone, role=User.ROLE_ADMIN, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur NOUNOU+.

    - phone       : identifiant unique (numéro de téléphone au format E.164, ex: +243812345678)
    - role        : client | travailleur | admin
    - otp_code    : empreinte du code SMS en cours (jamais le code en clair)
    - phone_verified : True une fois que l'utilisateur a validé son OTP
    """

    ROLE_CLIENT = "client"
    ROLE_WORKER = "travailleur"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_CLIENT, "Client"),
        (ROLE_WORKER, "Travailleur"),
        (ROLE_ADMIN, "Administrateur"),
    ]

    phone = PhoneNumberField(unique=True, verbose_name="Numéro de téléphone")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rôle")
    otp_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Code OTP (empreinte)",
        help_text="Empreinte du code à usage unique (le code lui-même n'est jamais stocké).",
    )
    otp_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Code valable jusqu'à")
    otp_attempts = models.PositiveSmallIntegerField(default=0, verbose_name="Essais sur le code en cours")
    phone_verified = models.BooleanField(
        default=False,
        verbose_name="Téléphone vérifié",
    )
    # --- Photo de profil (visible par tous après validation par l'équipe) ---
    PHOTO_NONE = "aucune"
    PHOTO_PENDING = "en_attente"
    PHOTO_APPROVED = "validee"
    PHOTO_REJECTED = "rejetee"
    PHOTO_STATUS_CHOICES = [
        (PHOTO_NONE, "Aucune photo"),
        (PHOTO_PENDING, "En attente de validation"),
        (PHOTO_APPROVED, "Validée"),
        (PHOTO_REJECTED, "Refusée"),
    ]
    photo = models.ImageField(upload_to="photos/", blank=True, verbose_name="Photo de profil")
    photo_status = models.CharField(
        max_length=20,
        choices=PHOTO_STATUS_CHOICES,
        default=PHOTO_NONE,
        verbose_name="Statut de la photo",
        help_text="La photo n'est montrée aux autres qu'une fois validée par l'équipe NOUNOU+.",
    )
    photo_rejection_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Motif du refus de la photo",
        help_text="Visible par la personne.",
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="E-mail",
        help_text="Facultatif : permet de se connecter avec un mot de passe.",
    )
    pending_email = models.EmailField(
        blank=True,
        default="",
        verbose_name="E-mail en attente de confirmation",
        help_text="Adresse saisie mais pas encore confirmée par le lien : elle ne sert à rien "
        "(ni connexion ni mot de passe oublié) et ne bloque personne.",
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name="E-mail vérifié",
        help_text="Lien de confirmation ouvert (ou adresse confirmée par Google / Apple).",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Compte actif",
        help_text="Décoché quand le compte est suspendu (plus de connexion possible).",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Équipe NOUNOU+",
        help_text="Peut se connecter à l'interface d'administration.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Inscrit le")
    token_version = models.PositiveIntegerField(
        default=0,
        verbose_name="Version des sessions",
        help_text="Augmente à chaque « déconnexion de tous les appareils » (ou changement de "
        "mot de passe) : les connexions ouvertes avant sont refusées.",
    )

    objects = UserManager()

    # Django utilise ce champ comme identifiant principal (login)
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # phone est déjà USERNAME_FIELD

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.phone} ({self.role})"

    def end_all_sessions(self) -> None:
        """Déconnecte tous les appareils (les jetons déjà émis sont refusés)."""
        self.token_version += 1
        self.save(update_fields=["token_version"])

    def save(self, *args, **kwargs):
        # Une adresse e-mail est enregistrée en minuscules (« Marie@Gmail.com » = « marie@gmail.com »)
        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = None  # plusieurs comptes sans e-mail ne doivent pas entrer en conflit
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Codes SMS
    # ------------------------------------------------------------------
    # Code aléatoire à 6 chiffres, stocké sous forme d'empreinte, valable 10 minutes,
    # 5 essais au plus. En développement (OTP_MOCK_ENABLED), le code est toujours 123456
    # et s'affiche dans la console ; en production il faut un fournisseur SMS (sms.py).

    OTP_MOCK_CODE = "123456"
    OTP_VALIDITY = timedelta(minutes=10)
    OTP_MAX_ATTEMPTS = 5

    @staticmethod
    def _otp_digest(code: str) -> str:
        return hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()

    def generate_otp(self) -> str:
        """Crée un nouveau code, l'envoie par SMS et le mémorise (empreinte seulement)."""
        from . import sms

        if not sms.available():
            raise OTPUnavailableError("Aucun service d'envoi de SMS n'est configuré.")
        code = self.OTP_MOCK_CODE if settings.OTP_MOCK_ENABLED else f"{secrets.randbelow(10**6):06d}"
        self.otp_code = self._otp_digest(code)
        self.otp_expires_at = timezone.now() + self.OTP_VALIDITY
        self.otp_attempts = 0
        self.save(update_fields=["otp_code", "otp_expires_at", "otp_attempts"])
        sms.send_code(str(self.phone), code)
        return code

    def verify_otp(self, code: str) -> bool:
        """Vérifie le code. Usage unique ; refusé après expiration ou 5 essais."""
        if not self.otp_code or not self.otp_expires_at or self.otp_expires_at < timezone.now():
            return False
        if self.otp_attempts >= self.OTP_MAX_ATTEMPTS:
            return False
        if not hmac.compare_digest(self.otp_code, self._otp_digest(code)):
            # Compté directement en base (deux essais simultanés comptent pour deux)
            User.objects.filter(pk=self.pk).update(otp_attempts=models.F("otp_attempts") + 1)
            return False
        self.otp_code = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.phone_verified = True
        self.save(update_fields=["otp_code", "otp_expires_at", "otp_attempts", "phone_verified"])
        return True


class PhotoToReview(User):
    """Vue « Photos à valider » dans l'administration (mêmes comptes, liste dédiée)."""

    class Meta:
        proxy = True
        verbose_name = "Photo de profil"
        verbose_name_plural = "Photos de profil"


class SocialAccount(models.Model):
    """Lien entre un compte NOUNOU+ et un compte Google ou Apple."""

    PROVIDER_GOOGLE = "google"
    PROVIDER_APPLE = "apple"
    PROVIDER_CHOICES = [(PROVIDER_GOOGLE, "Google"), (PROVIDER_APPLE, "Apple")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_accounts", verbose_name="Compte"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name="Service")
    uid = models.CharField(
        max_length=255,
        verbose_name="Identifiant chez le service",
        help_text="Identifiant fourni par Google ou Apple (jamais un mot de passe).",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Lié le")

    class Meta:
        verbose_name = "Compte Google / Apple"
        verbose_name_plural = "Comptes Google / Apple"
        constraints = [
            models.UniqueConstraint(fields=["provider", "uid"], name="unique_social_account"),
        ]

    def __str__(self):
        return f"{self.get_provider_display()} — {self.user}"
