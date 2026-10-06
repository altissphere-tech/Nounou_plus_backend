"""
Modèle JobRequest — annonce publiée par un client (famille).

Une famille peut publier plusieurs annonces, chacune pour un service précis
(ex : une nounou à temps plein ET une cuisinière le week-end).
Les travailleurs vérifiés y répondent en manifestant leur intérêt : cela crée
(ou complète) la mise en relation avec la famille, avec les mêmes règles de
confidentialité (coordonnées révélées seulement après un match mutuel).
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from common import choices


class JobRequestQuerySet(models.QuerySet):
    def open_to_workers(self):
        """Annonces ouvertes, publiées par des familles dont le compte est actif."""
        return self.filter(status=JobRequest.STATUS_OPEN, client__user__is_active=True)


class JobRequest(models.Model):
    STATUS_OPEN = "ouverte"
    STATUS_FILLED = "pourvue"
    STATUS_CLOSED = "fermee"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Ouverte"),
        (STATUS_FILLED, "Pourvue"),
        (STATUS_CLOSED, "Fermée"),
    ]

    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="job_requests",
        verbose_name="Client",
    )
    title = models.CharField(
        max_length=120,
        verbose_name="Titre",
        help_text="Ex : « Nounou pour 2 enfants, du lundi au vendredi ».",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="job_requests",
        verbose_name="Service demandé",
    )
    availability = models.CharField(
        max_length=20, choices=choices.AVAILABILITY_CHOICES, verbose_name="Disponibilité requise"
    )
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Budget mensuel",
        help_text="En francs congolais (CDF). Facultatif.",
    )
    location = models.CharField(
        max_length=200,
        verbose_name="Localisation",
        help_text="Quartier ou commune. Par défaut, celui du profil client.",
    )
    description = models.TextField(blank=True, default="", verbose_name="Description")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Publiée le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifiée le")

    objects = JobRequestQuerySet.as_manager()

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
