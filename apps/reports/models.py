"""
Modèle Report — signalement d'un profil par un utilisateur.

Règles validées par le fondateur :
- Tout utilisateur peut signaler un profil qu'il voit (listes ou matchs), sans besoin de match.
- Catégories : faux profil, comportement inapproprié / harcèlement, arnaque / demande
  d'argent, problème de sécurité, autre (description obligatoire).
- Le signalement est anonyme : la personne signalée ne sait jamais qui l'a signalée.
- L'administrateur décide : classer sans suite, avertir, ou suspendre le compte.
  Un compte suspendu ne peut plus se connecter et disparaît des listes.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

MAX_DESCRIPTION_LENGTH = 2000


class Report(models.Model):
    # --- Catégories ---
    CATEGORY_FAKE_PROFILE = "faux_profil"
    CATEGORY_BEHAVIOUR = "comportement_inapproprie"
    CATEGORY_SCAM = "arnaque"
    CATEGORY_SAFETY = "securite"
    CATEGORY_OTHER = "autre"

    CATEGORY_CHOICES = [
        (CATEGORY_FAKE_PROFILE, "Faux profil"),
        (CATEGORY_BEHAVIOUR, "Comportement inapproprié / harcèlement"),
        (CATEGORY_SCAM, "Arnaque / demande d'argent"),
        (CATEGORY_SAFETY, "Problème de sécurité"),
        (CATEGORY_OTHER, "Autre"),
    ]

    # --- Statuts (décision de l'administrateur) ---
    STATUS_PENDING = "en_attente"
    STATUS_DISMISSED = "classe_sans_suite"
    STATUS_WARNED = "avertissement"
    STATUS_SUSPENDED = "suspendu"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_DISMISSED, "Classé sans suite"),
        (STATUS_WARNED, "Avertissement envoyé"),
        (STATUS_SUSPENDED, "Compte suspendu"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
        verbose_name="Auteur du signalement",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
        verbose_name="Personne signalée",
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name="Catégorie")
    description = models.TextField(
        blank=True, default="", max_length=MAX_DESCRIPTION_LENGTH, verbose_name="Description"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Décision"
    )
    user_message = models.TextField(
        blank=True,
        default="",
        verbose_name="Message à la personne signalée",
        help_text=(
            "En cas d'avertissement, ce message est affiché à la personne signalée "
            "(sans jamais révéler qui l'a signalée)."
        ),
    )
    admin_note = models.TextField(
        blank=True, default="", verbose_name="Note interne", help_text="Visible uniquement par l'équipe."
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_decided",
        verbose_name="Traité par",
    )
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name="Traité le")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")

    class Meta:
        verbose_name = "Signalement"
        verbose_name_plural = "Signalements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} — {self.target.phone} ({self.get_status_display()})"

    def decide(self, admin_user, status: str, user_message: str = "", previous_status: str = None) -> None:
        """
        Enregistre la décision de l'administrateur et applique ses effets sur le compte :
        - « suspendu » désactive le compte (plus de connexion, disparition des listes) ;
        - si une suspension est annulée, le compte est réactivé, sauf si un autre
          signalement le maintient suspendu.
        """
        previous_status = previous_status or self.status
        self.status = status
        if status == self.STATUS_WARNED and not user_message.strip():
            user_message = (
                "Votre comportement a fait l'objet d'un signalement. Merci de respecter "
                "les règles de la communauté NOUNOU+."
            )
        self.user_message = user_message if status == self.STATUS_WARNED else ""
        self.decided_by = admin_user if status != self.STATUS_PENDING else None
        self.decided_at = timezone.now() if status != self.STATUS_PENDING else None
        self.save()

        target = self.target
        if status != previous_status:
            from common.security_log import event

            event("signalement_decide", decision=status, compte=target.pk, par=getattr(admin_user, "pk", "-"))
        if status == self.STATUS_WARNED and previous_status != self.STATUS_WARNED:
            from apps.notifications.models import Notification, notify

            notify(target, Notification.KIND_WARNING)
        if status == self.STATUS_SUSPENDED and target.is_active:
            target.is_active = False
            target.save(update_fields=["is_active"])
        elif previous_status == self.STATUS_SUSPENDED and status != self.STATUS_SUSPENDED:
            still_suspended = target.reports_received.filter(status=self.STATUS_SUSPENDED).exists()
            if not still_suspended and not target.is_active:
                target.is_active = True
                target.save(update_fields=["is_active"])


def warnings_for(user) -> list[dict]:
    """Avertissements reçus par un utilisateur (affichés sur son compte, sans l'auteur)."""
    reports = user.reports_received.filter(status=Report.STATUS_WARNED).order_by("-decided_at")
    return [{"message": r.user_message, "date": r.decided_at} for r in reports]
