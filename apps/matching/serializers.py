"""
Serializers de l'app matching.

Point clé : les informations sur l'autre partie dépendent du statut du match.
- Avant un match mutuel : prénom + initiale du nom, téléphone absent.
- Après un match mutuel : nom complet et téléphone.
"""
from datetime import datetime

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.clients.serializers import ClientProfilePublicSerializer, ClientProfileSerializer
from apps.workers.serializers import WorkerProfilePublicSerializer, WorkerProfileSerializer

from .models import Match


class InterestSerializer(serializers.Serializer):
    """Données envoyées pour manifester son intérêt."""

    profile_id = serializers.IntegerField(
        help_text=(
            "Identifiant du profil qui vous intéresse : un profil travailleur "
            "si vous êtes client, un profil client si vous êtes travailleur."
        )
    )


class JobSummarySerializer(serializers.Serializer):
    """Annonce à l'origine d'une mise en relation (format court)."""

    id = serializers.IntegerField()
    title = serializers.CharField()


class MatchSerializer(serializers.ModelSerializer):
    """
    Un match vu par l'utilisateur connecté (le contexte doit contenir `request`).
    """

    status = serializers.SerializerMethodField()
    my_decision = serializers.SerializerMethodField()
    their_decision = serializers.SerializerMethodField()
    other_party = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField(
        help_text="Nombre de messages reçus non lus (0 si le match n'est pas mutuel)."
    )

    job = serializers.SerializerMethodField(
        help_text="Annonce concernée {id, title} ou null si le contact est direct."
    )
    can_review = serializers.SerializerMethodField(
        help_text="True si vous pouvez maintenant évaluer l'autre personne."
    )
    review_available_at = serializers.DateTimeField(
        read_only=True,
        help_text="Date à partir de laquelle l'évaluation est possible (null si jamais mutuel).",
    )
    updated_at = serializers.SerializerMethodField(
        help_text="Dernière activité visible par vous (un refus de l'autre n'y apparaît jamais)."
    )

    class Meta:
        model = Match
        fields = [
            "id",
            "status",
            "my_decision",
            "their_decision",
            "other_party",
            "job",
            "unread_count",
            "can_review",
            "review_available_at",
            "mutual_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _user(self):
        return self.context["request"].user

    def get_status(self, obj) -> str:
        return obj.status_seen_by(self._user())

    def get_updated_at(self, obj) -> datetime:
        return obj.visible_activity_for(self._user())

    def get_my_decision(self, obj) -> str:
        return obj.decision_of(self._user())

    def get_their_decision(self, obj) -> str:
        return obj.other_decision_seen_by(self._user())

    @extend_schema_field(JobSummarySerializer(allow_null=True))
    def get_job(self, obj):
        if obj.job_id is None:
            return None
        return {"id": obj.job_id, "title": obj.job.title}

    def get_can_review(self, obj) -> bool:
        return obj.can_be_reviewed_by(self._user())

    def get_unread_count(self, obj) -> int:
        user = self._user()
        if obj.status_seen_by(user) != Match.STATUS_MUTUAL:
            return 0
        return obj.messages.filter(read_at__isnull=True).exclude(sender=user).count()

    def get_other_party(self, obj) -> dict:
        user = self._user()
        mutual = obj.status_seen_by(user) == Match.STATUS_MUTUAL
        if obj.is_client_side(user):
            profile = obj.worker
            serializer_class = WorkerProfileSerializer if mutual else WorkerProfilePublicSerializer
        else:
            profile = obj.client
            serializer_class = ClientProfileSerializer if mutual else ClientProfilePublicSerializer
        data = dict(serializer_class(profile).data)
        # Le téléphone complet n'est révélé qu'après un match mutuel
        data["phone"] = str(profile.user.phone) if mutual else None
        return data
