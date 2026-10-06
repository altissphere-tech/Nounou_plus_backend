"""
Modèle Match — mise en relation entre un client et un travailleur.

Fonctionnement (règles validées par le fondateur) :
1. Le client ou le travailleur clique sur « intéressé ».
2. Si l'autre clique aussi, c'est un match mutuel : nom complet et téléphone
   deviennent visibles (et la messagerie pourra s'ouvrir).
3. Chacun peut refuser. L'autre personne n'est jamais prévenue du refus :
   pour elle, la demande reste simplement « en attente ».
"""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import User


class MatchQuerySet(models.QuerySet):
    def for_user(self, user):
        """
        Les matchs auxquels l'utilisateur participe, en excluant ceux dont
        l'autre partie a un compte suspendu (elle disparaît de la plateforme).
        """
        return self.filter(
            models.Q(client__user=user) | models.Q(worker__user=user),
            client__user__is_active=True,
            worker__user__is_active=True,
        ).select_related("client__user", "worker__user")


class Match(models.Model):
    # --- Décision de chaque partie ---
    DECISION_PENDING = "en_attente"
    DECISION_INTERESTED = "interesse"
    DECISION_DECLINED = "refuse"

    DECISION_CHOICES = [
        (DECISION_PENDING, "En attente"),
        (DECISION_INTERESTED, "Intéressé"),
        (DECISION_DECLINED, "Refusé"),
    ]

    # --- Statut global du match ---
    STATUS_PENDING = "en_attente"
    STATUS_MUTUAL = "mutuel"
    STATUS_DECLINED = "refuse"

    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="matches",
        verbose_name="Client",
    )
    worker = models.ForeignKey(
        "workers.WorkerProfile",
        on_delete=models.CASCADE,
        related_name="matches",
        verbose_name="Travailleur",
    )
    client_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default=DECISION_PENDING,
        verbose_name="Décision du client",
    )
    worker_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default=DECISION_PENDING,
        verbose_name="Décision du travailleur",
    )
    mutual_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Match mutuel le",
        help_text="Date à laquelle les deux parties se sont déclarées intéressées.",
    )
    first_mutual_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Premier match mutuel le",
        help_text=(
            "Date du tout premier match mutuel, jamais effacée. "
            "Sert à calculer quand les deux parties peuvent s'évaluer."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    objects = MatchQuerySet.as_manager()

    class Meta:
        verbose_name = "Mise en relation"
        verbose_name_plural = "Mises en relation"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "worker"], name="unique_match_client_worker"
            ),
        ]

    def __str__(self):
        return f"{self.client} ↔ {self.worker} ({self.status})"

    # ------------------------------------------------------------------
    # Statut
    # ------------------------------------------------------------------

    @property
    def status(self) -> str:
        """Statut réel du match (vu par l'administrateur)."""
        decisions = {self.client_decision, self.worker_decision}
        if self.DECISION_DECLINED in decisions:
            return self.STATUS_DECLINED
        if decisions == {self.DECISION_INTERESTED}:
            return self.STATUS_MUTUAL
        return self.STATUS_PENDING

    @property
    def is_mutual(self) -> bool:
        return self.status == self.STATUS_MUTUAL

    # ------------------------------------------------------------------
    # Point de vue d'un utilisateur
    # ------------------------------------------------------------------

    def is_client_side(self, user) -> bool:
        """True si l'utilisateur est le client de ce match, False s'il est le travailleur."""
        return user.role == User.ROLE_CLIENT

    def decision_of(self, user) -> str:
        return self.client_decision if self.is_client_side(user) else self.worker_decision

    def other_decision_seen_by(self, user) -> str:
        """
        Décision de l'autre partie, telle que l'utilisateur a le droit de la voir.
        Un refus de l'autre est présenté comme « en attente » (jamais révélé).
        """
        other = self.worker_decision if self.is_client_side(user) else self.client_decision
        return self.DECISION_PENDING if other == self.DECISION_DECLINED else other

    def status_seen_by(self, user) -> str:
        """Statut du match tel que l'utilisateur a le droit de le voir."""
        if self.decision_of(user) == self.DECISION_DECLINED:
            return self.STATUS_DECLINED
        if self.is_mutual:
            return self.STATUS_MUTUAL
        return self.STATUS_PENDING

    def set_decision(self, user, decision: str) -> None:
        """Enregistre la décision de l'utilisateur et met à jour la date du match mutuel."""
        if self.is_client_side(user):
            self.client_decision = decision
        else:
            self.worker_decision = decision
        if not self.is_mutual:
            # Si l'une des parties revient sur sa décision, les coordonnées
            # ne sont plus partagées et la date du match est effacée
            self.mutual_at = None
        elif self.mutual_at is None:
            self.mutual_at = timezone.now()
            if self.first_mutual_at is None:
                self.first_mutual_at = self.mutual_at
        self.save()

    # ------------------------------------------------------------------
    # Évaluation après la période d'essai
    # ------------------------------------------------------------------

    @property
    def review_available_at(self):
        """Date à partir de laquelle les deux parties peuvent s'évaluer (None si jamais mutuel)."""
        if self.first_mutual_at is None:
            return None
        return self.first_mutual_at + timedelta(days=settings.REVIEW_DELAY_DAYS)

    def can_be_reviewed_by(self, user) -> bool:
        """
        True si l'utilisateur peut évaluer l'autre partie : le match a été mutuel,
        le délai d'essai est écoulé, et il n'a pas déjà laissé d'avis.
        """
        available_at = self.review_available_at
        if available_at is None or timezone.now() < available_at:
            return False
        return not self.reviews.filter(author=user).exists()
