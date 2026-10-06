"""
Notifications dans l'application (cloche en haut de l'écran).

Pas de SMS ni de notification « push » en V1 : la personne les voit en ouvrant
l'application. Le texte n'est pas stocké : seuls le type et quelques valeurs le sont,
et l'application affiche la phrase dans la langue choisie (français ou anglais).

Confidentialité : le nom affiché suit les mêmes règles que le reste de l'application
(prénom + initiale du nom avant un match mutuel). Un refus n'est jamais notifié.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    KIND_INTEREST = "interest_received"  # quelqu'un s'intéresse à vous
    KIND_MATCH = "match_mutual"  # c'est un match
    KIND_MESSAGE = "new_message"  # nouveau(x) message(s)
    KIND_DOCUMENT = "document_reviewed"  # document validé / refusé
    KIND_PHOTO = "photo_reviewed"  # photo validée / refusée
    KIND_REFERENCE = "reference_reviewed"  # référence vérifiée / non confirmée
    KIND_WARNING = "warning"  # avertissement de l'équipe

    KIND_CHOICES = [
        (KIND_INTEREST, "Intérêt reçu"),
        (KIND_MATCH, "Match mutuel"),
        (KIND_MESSAGE, "Nouveau message"),
        (KIND_DOCUMENT, "Document examiné"),
        (KIND_PHOTO, "Photo examinée"),
        (KIND_REFERENCE, "Référence examinée"),
        (KIND_WARNING, "Avertissement"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire",
    )
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, verbose_name="Type")
    params = models.JSONField(default=dict, blank=True, verbose_name="Détails")
    count = models.PositiveIntegerField(default=1, verbose_name="Nombre (messages regroupés)")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lue le")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "read_at"])]

    def __str__(self):
        return f"{self.get_kind_display()} → {self.user}"


def notify(user, kind: str, **params) -> Notification:
    """
    Crée une notification. Les nouveaux messages d'une même conversation sont
    regroupés tant qu'ils ne sont pas lus (« 3 nouveaux messages de Grâce M. »).
    """
    if kind == Notification.KIND_MESSAGE:
        existing = Notification.objects.filter(
            user=user, kind=kind, read_at__isnull=True, params__match_id=params.get("match_id")
        ).first()
        if existing:
            existing.count += 1
            existing.params = params
            existing.created_at = timezone.now()
            existing.save(update_fields=["count", "params", "created_at"])
            return existing
    return Notification.objects.create(user=user, kind=kind, params=params)


def display_name(profile, full: bool) -> str:
    """Nom montré dans une notification : complet seulement après un match mutuel."""
    from common.privacy import mask_last_name

    if profile is None:
        return ""
    last = profile.last_name if full else mask_last_name(profile.last_name)
    return f"{profile.first_name} {last}".strip()
