"""
Modèle User personnalisé pour NOUNOU+.

Pourquoi personnaliser ? Django utilise l'email ou un nom d'utilisateur par défaut.
Ici, l'identifiant unique est le numéro de téléphone (adapté au contexte RDC).
"""
import logging
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    """Gestionnaire du modèle User — remplace le manager par défaut de Django."""

    def create_user(self, phone, role, password=None, **extra_fields):
        if not phone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        if role not in [User.ROLE_CLIENT, User.ROLE_WORKER, User.ROLE_ADMIN]:
            raise ValueError(f"Rôle invalide : {role}")
        user = self.model(phone=phone, role=role, **extra_fields)
        # En V1, pas de mot de passe : l'authentification se fait uniquement par OTP.
        # On fixe un mot de passe inutilisable pour respecter le contrat Django.
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # Django utilise ce champ comme identifiant principal (login)
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # phone est déjà USERNAME_FIELD

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.phone} ({self.role})"

    # ------------------------------------------------------------------
    # Logique OTP (simulée en V1)
    # ------------------------------------------------------------------

    OTP_MOCK_CODE = "123456"

    def generate_otp(self) -> str:
        """
        Génère et stocke un OTP.
        En V1 : toujours '123456'. En V2, remplacer par un vrai générateur + SMS.
        """
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
        if self.otp_code and self.otp_code == code:
            self.otp_code = None
            self.phone_verified = True
            self.save(update_fields=["otp_code", "phone_verified"])
            return True
        return False
