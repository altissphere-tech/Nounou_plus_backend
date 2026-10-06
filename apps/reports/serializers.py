"""
Serializers de l'app reports.
"""
from rest_framework import serializers

from .models import MAX_DESCRIPTION_LENGTH, Report


class ReportCreateSerializer(serializers.Serializer):
    profile_id = serializers.IntegerField(
        help_text=(
            "Identifiant du profil signalé : un profil travailleur si vous êtes client, "
            "un profil client si vous êtes travailleur."
        )
    )
    category = serializers.ChoiceField(choices=Report.CATEGORY_CHOICES)
    description = serializers.CharField(
        max_length=MAX_DESCRIPTION_LENGTH, required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        if attrs["category"] == Report.CATEGORY_OTHER and not attrs["description"].strip():
            raise serializers.ValidationError(
                {"description": "Merci de décrire le problème (obligatoire pour « Autre »)."}
            )
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    """
    Un signalement vu par son auteur. Le détail de la décision n'est pas montré
    (il concerne la personne signalée) : seulement « en attente » ou « traité ».
    """

    status = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ["id", "category", "description", "status", "created_at"]
        read_only_fields = fields

    def get_status(self, obj) -> str:
        return "en_attente" if obj.status == Report.STATUS_PENDING else "traite"
