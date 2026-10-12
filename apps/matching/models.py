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
from django.db import models, transaction
from django.db.models import Case, F, When
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone

from apps.accounts.models import User


class MatchQuerySet(models.QuerySet):
    def for_user(self, user):
        """
        Les matchs auxquels l'utilisateur participe, en excluant ceux dont
        l'autre partie a un compte suspendu ou un numéro non confirmé (elle
        disparaît de la plateforme).
        """
        return self.filter(
            models.Q(client__user=user) | models.Q(worker__user=user),
            client__user__is_active=True,
            worker__user__is_active=True,
            client__user__phone_verified=True,
            worker__user__phone_verified=True,
        ).select_related("client__user", "worker__user", "job")

    def ordered_for(self, user):
        """
        Du plus récent au plus ancien, selon ce que l'utilisateur a le droit de voir :
        un refus de l'autre ne fait jamais remonter la mise en relation (il resterait
        sinon devinable).
        """
        client_side = user.role == User.ROLE_CLIENT
        own, other = ("client", "worker") if client_side else ("worker", "client")
        created = F("created_at")
        return self.annotate(
            visible_activity=Greatest(
                created,
                Coalesce(F(f"{own}_activity_at"), created),
                Case(
                    When(**{f"{other}_decision": Match.DECISION_INTERESTED},
                         then=Coalesce(F(f"{other}_activity_at"), created)),
                    default=created,
                ),
                Coalesce(F("mutual_at"), created),
            )
        ).order_by("-visible_activity", "-id")


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
    job = models.ForeignKey(
        "jobs.JobRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
        verbose_name="Annonce concernée",
        help_text="Annonce à laquelle le travailleur a répondu (vide si contact direct).",
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
    mutual_duration = models.DurationField(
        default=timedelta(0),
        verbose_name="Durée cumulée des périodes mutuelles terminées",
        help_text=(
            "Ajoutée à chaque retrait d'un accord mutuel. Un avis n'est possible "
            "qu'après un accord resté actif au moins le délai d'essai."
        ),
    )
    client_activity_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière décision du client le"
    )
    worker_activity_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière décision du travailleur le"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le",
        help_text="Réservé à l'équipe : jamais montré aux utilisateurs (un refus s'y lirait).",
    )

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

    def contact_open_for(self, user) -> bool:
        """
        True si l'utilisateur voit les coordonnées de l'autre partie et accède à la
        messagerie : match mutuel et, côté travailleur, profil toujours vérifié. Un
        travailleur qui perd son badge perd cet accès jusqu'à une nouvelle vérification
        (décision du fondateur, octobre 2026).
        """
        if self.status_seen_by(user) != self.STATUS_MUTUAL:
            return False
        return self.is_client_side(user) or self.worker.is_verified

    def visible_activity_for(self, user):
        """Date de dernière activité telle que l'utilisateur a le droit de la voir."""
        client_side = self.is_client_side(user)
        own = self.client_activity_at if client_side else self.worker_activity_at
        other = self.worker_activity_at if client_side else self.client_activity_at
        other_decision = self.worker_decision if client_side else self.client_decision
        dates = [self.created_at, own, self.mutual_at]
        if other_decision == self.DECISION_INTERESTED:
            dates.append(other)
        return max(d for d in dates if d is not None)

    def set_decision(self, user, decision: str) -> tuple[str, bool]:
        """
        Enregistre la décision de l'utilisateur et met à jour la date du match mutuel.
        La ligne est relue et verrouillée : si l'autre personne décide au même instant,
        sa décision n'est jamais écrasée. Renvoie (ancienne décision, était mutuel).
        """
        own = "client" if self.is_client_side(user) else "worker"
        with transaction.atomic():
            current = Match.objects.select_for_update().get(pk=self.pk)
            previous, was_mutual = getattr(current, f"{own}_decision"), current.is_mutual
            now = timezone.now()
            setattr(current, f"{own}_decision", decision)
            setattr(current, f"{own}_activity_at", now)
            if not current.is_mutual:
                # Si l'une des parties revient sur sa décision, les coordonnées
                # ne sont plus partagées et la date du match est effacée ; la durée
                # de l'accord qui se termine est gardée (calcul du droit à l'avis)
                if current.mutual_at is not None:
                    current.mutual_duration += now - current.mutual_at
                current.mutual_at = None
            elif current.mutual_at is None:
                current.mutual_at = now
                if current.first_mutual_at is None:
                    current.first_mutual_at = now
            current.save(
                update_fields=[
                    f"{own}_decision", f"{own}_activity_at", "mutual_at", "first_mutual_at",
                    "mutual_duration", "updated_at",
                ]
            )
        for field in ("client_decision", "worker_decision", "client_activity_at", "worker_activity_at",
                      "mutual_at", "first_mutual_at", "mutual_duration", "updated_at"):
            setattr(self, field, getattr(current, field))
        return previous, was_mutual

    # ------------------------------------------------------------------
    # Évaluation après la période d'essai
    # ------------------------------------------------------------------

    @property
    def review_available_at(self):
        """
        Date à partir de laquelle les deux parties peuvent s'évaluer, ou None.
        L'accord doit être resté actif au moins REVIEW_DELAY_DAYS jours au total
        (décision du fondateur, octobre 2026) : un accord retiré au bout d'une seconde
        ne permet pas de laisser un avis.
        """
        delay = timedelta(days=settings.REVIEW_DELAY_DAYS)
        if self.first_mutual_at is None:
            return None
        if self.mutual_at is not None:  # accord en cours : il reste le temps manquant
            return self.mutual_at + max(delay - self.mutual_duration, timedelta(0))
        if self.mutual_duration >= delay:  # accord terminé, assez long : déjà atteint
            return self.first_mutual_at + delay
        return None

    def can_be_reviewed_by(self, user) -> bool:
        """
        True si l'utilisateur peut évaluer l'autre partie : le match a été mutuel,
        le délai d'essai est écoulé, et il n'a pas déjà laissé d'avis.
        """
        available_at = self.review_available_at
        if available_at is None or timezone.now() < available_at:
            return False
        return not self.reviews.filter(author=user).exists()
