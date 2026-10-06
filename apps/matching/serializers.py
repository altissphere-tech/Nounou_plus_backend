"""
Serializers de l'app matching.

Point clé : les informations sur l'autre partie dépendent du statut du match.
- Avant un match mutuel : prénom + initiale du nom, téléphone absent.
- Après un match mutuel : nom complet et téléphone.
"""
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


class MatchSerializer(serializers.ModelSerializer):
    """
    Un match vu par l'utilisateur connecté (le contexte doit contenir `request`).
    """

    status = serializers.SerializerMethodField()
    my_decision = serializers.SerializerMethodField()
    their_decision = serializers.SerializerMethodField()
    other_party = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            "id",
            "status",
            "my_decision",
            "their_decision",
            "other_party",
            "mutual_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _user(self):
        return self.context["request"].user

    def get_status(self, obj) -> str:
        return obj.status_seen_by(self._user())

    def get_my_decision(self, obj) -> str:
        return obj.decision_of(self._user())

    def get_their_decision(self, obj) -> str:
        return obj.other_decision_seen_by(self._user())

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
