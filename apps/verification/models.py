"""
Modèle VerificationRecord — documents envoyés par un travailleur pour obtenir le badge « vérifié ».

Règles validées par le fondateur :
- Documents : pièce d'identité (obligatoire pour le badge) et lettre de référence (facultative).
- Seul l'administrateur voit les documents. Les clients ne voient que le badge.
- Le badge « vérifié » est accordé dès que l'admin valide une pièce d'identité.
  Rappel : ce badge ne constitue pas une garantie d'absence de risque.

Stockage : les fichiers passent par le stockage de fichiers de Django (disque local
en développement), remplaçable plus tard par un stockage compatible S3 sans changer ce code.
Ils ne sont jamais servis par une adresse publique : l'admin les ouvre via une page protégée.
"""
import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
MAX_FILE_SIZE_MB = 5


def document_upload_path(instance, filename: str) -> str:
    """
    Range le fichier dans verification/<id du travailleur>/<nom aléatoire>.<extension>.
    Le nom d'origine n'est pas conservé (il peut contenir des données personnelles).
    """
    extension = Path(filename).suffix.lower()
    return f"verification/{instance.worker_id}/{uuid.uuid4().hex}{extension}"


class VerificationRecord(models.Model):
    # --- Types de documents ---
    TYPE_IDENTITY = "identite"
    TYPE_REFERENCE = "reference"

    TYPE_CHOICES = [
        (TYPE_IDENTITY, "Pièce d'identité"),
        (TYPE_REFERENCE, "Lettre de référence"),
    ]

    # --- Statuts ---
    STATUS_PENDING = "en_attente"
    STATUS_APPROVED = "valide"
    STATUS_REJECTED = "rejete"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_APPROVED, "Validé"),
        (STATUS_REJECTED, "Rejeté"),
    ]

    worker = models.ForeignKey(
        "workers.WorkerProfile",
        on_delete=models.CASCADE,
        related_name="verification_records",
        verbose_name="Travailleur",
    )
    doc_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de document")
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(ALLOWED_EXTENSIONS)],
        verbose_name="Fichier",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Statut"
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Motif du rejet",
        help_text="Visible par le travailleur si le document est rejeté.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_documents",
        verbose_name="Examiné par",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Examiné le")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")

    class Meta:
        verbose_name = "Document de vérification"
        verbose_name_plural = "Documents de vérification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_doc_type_display()} — {self.worker} ({self.get_status_display()})"

    def review(self, admin_user, status: str, reason: str = "") -> None:
        """Enregistre la décision de l'administrateur et met à jour le badge du travailleur."""
        self.status = status
        self.rejection_reason = reason if status == self.STATUS_REJECTED else ""
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        update_worker_badge(self.worker)


def update_worker_badge(worker) -> None:
    """
    Le badge « vérifié » suit les pièces d'identité : il est actif tant qu'au moins
    une pièce d'identité du travailleur est validée.
    """
    has_valid_identity = worker.verification_records.filter(
        doc_type=VerificationRecord.TYPE_IDENTITY,
        status=VerificationRecord.STATUS_APPROVED,
    ).exists()
    if worker.is_verified != has_valid_identity:
        worker.is_verified = has_valid_identity
        worker.save(update_fields=["is_verified", "updated_at"])


@receiver(post_delete, sender=VerificationRecord)
def delete_document_file(sender, instance, **kwargs):
    """Supprime le fichier du disque quand le document est supprimé (données personnelles)."""
    if instance.file:
        instance.file.delete(save=False)
