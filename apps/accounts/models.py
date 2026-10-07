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
import logging
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
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
    - otp_code    : code OTP actuel (simulé en V1 : toujours '123456')
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
        max_length=6,
        blank=True,
        null=True,
        verbose_name="Code OTP",
        help_text="Code à usage unique pour vérifier le numéro de téléphone.",
    )
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
    # Logique OTP (simulée en V1)
    # ------------------------------------------------------------------

    OTP_MOCK_CODE = "123456"

    def generate_otp(self) -> str:
        """
        Génère et stocke un OTP.
        En V1 : toujours '123456'. En V2, remplacer par un vrai générateur + SMS.
        Refuse de fonctionner si OTP_MOCK_ENABLED est désactivé (production).
        """
        if not settings.OTP_MOCK_ENABLED:
            raise OTPUnavailableError("Aucun service d'envoi d'OTP n'est configuré.")
        self.otp_code = self.OTP_MOCK_CODE
        self.save(update_fields=["otp_code"])
        # Affiche le code en console (visible dans les logs du serveur en dev)
        logger.warning(
            "[OTP SIMULÉ] Numéro %s → code OTP : %s (V1 uniquement, ne pas utiliser en production)",
            self.phone,
            self.otp_code,
        )
        return self.otp_code

    def verify_otp(self, code: str) -> bool:
        """Vérifie le code OTP soumis par l'utilisateur. Efface le code après succès."""
        if not settings.OTP_MOCK_ENABLED:
            return False
        if self.otp_code and self.otp_code == code:
            self.otp_code = None
            self.phone_verified = True
            self.save(update_fields=["otp_code", "phone_verified"])
            return True
        return False


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
