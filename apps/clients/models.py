"""
Modèle ClientProfile — profil d'une famille (client) qui cherche un travailleur domestique.

Lié en OneToOne à un User de rôle "client".
Un client ne peut avoir qu'un seul profil.
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from common import choices


class ClientProfileQuerySet(models.QuerySet):
    def active(self):
        """Profils dont le compte n'est pas suspendu."""
        return self.filter(user__is_active=True)


class ClientProfile(models.Model):
    """
    Profil d'un client (famille) et description de ses besoins.

    Règle métier : le nom de famille et le téléphone restent masqués pour
    les travailleurs tant qu'il n'y a pas de match mutuel (module matching).
    """

    # --- Lien vers le compte utilisateur ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile",
        verbose_name="Compte utilisateur",
    )

    # --- Informations personnelles ---
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    location = models.CharField(
        max_length=200,
        verbose_name="Localisation",
        help_text="Quartier ou commune à Lubumbashi.",
    )

    # --- Besoins ---
    services_needed = models.ManyToManyField(
        "services.Service",
        related_name="clients",
        verbose_name="Services recherchés",
    )
    availability_needed = models.CharField(
        max_length=20,
        choices=choices.AVAILABILITY_CHOICES,
        verbose_name="Disponibilité recherchée",
    )
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Budget mensuel",
        help_text="Montant mensuel envisagé, en francs congolais (CDF). Facultatif.",
    )
    needs_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description des besoins",
        help_text="Ex : 2 enfants de 3 et 6 ans, du lundi au vendredi.",
    )

    # --- Horodatages ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    objects = ClientProfileQuerySet.as_manager()

    class Meta:
        verbose_name = "Profil client"
        verbose_name_plural = "Profils clients"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone})"

    def get_services_list(self) -> list[str]:
        """Retourne la liste des slugs des services recherchés."""
        return list(self.services_needed.values_list("slug", flat=True))
