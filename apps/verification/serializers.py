"""
Serializers de l'app verification.

Le fichier lui-même n'est jamais renvoyé dans l'API : seul l'administrateur peut l'ouvrir.
"""
from rest_framework import serializers

from .models import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, VerificationRecord


class VerificationRecordSerializer(serializers.ModelSerializer):
    """Un document vu par le travailleur qui l'a envoyé (sans le fichier)."""

    class Meta:
        model = VerificationRecord
        fields = ["id", "doc_type", "status", "rejection_reason", "reviewed_at", "created_at"]
        read_only_fields = fields


class VerificationUploadSerializer(serializers.ModelSerializer):
    """Envoi d'un document (formulaire multipart : doc_type + file)."""

    class Meta:
        model = VerificationRecord
        fields = ["doc_type", "file"]
        extra_kwargs = {
            "file": {
                "help_text": (
                    f"Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)} — "
                    f"{MAX_FILE_SIZE_MB} Mo maximum."
                )
            }
        }

    def validate_file(self, value):
        if value.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Le fichier dépasse la taille maximale de {MAX_FILE_SIZE_MB} Mo."
            )
        return value

    def validate_doc_type(self, value):
        worker = self.context["worker"]
        existing = worker.verification_records.filter(doc_type=value)
        if existing.filter(status=VerificationRecord.STATUS_PENDING).exists():
            raise serializers.ValidationError(
                "Un document de ce type est déjà en attente de vérification."
            )
        if existing.filter(status=VerificationRecord.STATUS_APPROVED).exists():
            raise serializers.ValidationError("Un document de ce type a déjà été validé.")
        return value

    def create(self, validated_data):
        return VerificationRecord.objects.create(worker=self.context["worker"], **validated_data)
