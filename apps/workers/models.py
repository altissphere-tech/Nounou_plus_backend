"""
Modèle WorkerProfile — profil complet d'un travailleur domestique.

Lié en OneToOne à un User de rôle "travailleur".
Un travailleur ne peut avoir qu'un seul profil.
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common import choices


class WorkerProfileQuerySet(models.QuerySet):
    def active(self):
        """Profils dont le compte n'est pas suspendu."""
        return self.filter(user__is_active=True)

    def visible_to_clients(self):
        """Profils que les clients peuvent voir : comptes actifs et vérifiés."""
        return self.active().filter(is_verified=True)


class WorkerProfile(models.Model):
    """
    Profil professionnel d'un travailleur domestique (nounou, femme de ménage, cuisinière).

    Règles métier importantes :
    - Le champ `is_verified` ne peut être mis à True que par un administrateur.
    - Les coordonnées personnelles (téléphone) restent masquées tant qu'il n'y a
      pas de match mutuel (géré au niveau des serializers/views du module matching).
    """

    # --- Choix de services proposés ---
    SERVICE_NOUNOU = "nounou"
    SERVICE_MENAGE = "menage"
    SERVICE_CUISINE = "cuisine"

    SERVICE_CHOICES = [
        (SERVICE_NOUNOU, "Garde d'enfants (nounou)"),
        (SERVICE_MENAGE, "Ménage / entretien"),
        (SERVICE_CUISINE, "Cuisine"),
    ]

    # --- Choix de disponibilité ---
    # (définis dans common/choices.py, partagés avec les profils clients)
    AVAILABILITY_FULL = choices.AVAILABILITY_FULL
    AVAILABILITY_PART = choices.AVAILABILITY_PART
    AVAILABILITY_WEEKEND = choices.AVAILABILITY_WEEKEND
    AVAILABILITY_CHOICES = choices.AVAILABILITY_CHOICES

    # --- Lien vers le compte utilisateur ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="worker_profile",
        verbose_name="Compte utilisateur",
    )

    # --- Informations personnelles ---
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    bio = models.TextField(
        blank=True,
        default="",
        verbose_name="Présentation",
        help_text="Quelques phrases pour se présenter aux familles.",
    )

    # --- Informations professionnelles ---
    # Les services sont liés via une relation M2M vers le modèle Service.
    # Permet de filtrer avec l'ORM : WorkerProfile.objects.filter(services__slug='nounou')
    services = models.ManyToManyField(
        "services.Service",
        related_name="workers",
        verbose_name="Services proposés",
    )
    years_experience = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name="Années d'expérience",
    )
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        verbose_name="Disponibilité",
    )
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Prétention salariale",
        help_text="Montant mensuel souhaité (en USD ou CDF selon accord).",
    )
    location = models.CharField(
        max_length=200,
        verbose_name="Localisation",
        help_text="Quartier ou commune à Lubumbashi.",
    )

    # --- Statut de vérification (géré par l'admin uniquement) ---
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Profil vérifié",
        help_text=(
            "Indique qu'un administrateur a vérifié les documents de ce travailleur. "
            "Ce badge ne constitue pas une garantie d'absence de risque."
        ),
    )

    # --- Horodatages ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    objects = WorkerProfileQuerySet.as_manager()

    class Meta:
        verbose_name = "Profil travailleur"
        verbose_name_plural = "Profils travailleurs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone})"

    def get_services_list(self) -> list[str]:
        """Retourne la liste des slugs des services proposés."""
        return list(self.services.values_list("slug", flat=True))
