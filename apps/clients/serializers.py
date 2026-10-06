"""
Serializers de l'app clients.

- ClientProfileSerializer      : lecture (son propre profil)
- ClientProfileWriteSerializer : écriture (création et modification)
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.photos import public_photo_url
from apps.services.models import Service
from apps.reviews.models import rating_summary
from apps.reviews.serializers import RatingSummarySerializer
from apps.services.serializers import validate_service_slugs
from common.privacy import mask_last_name

from .models import ClientProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    """Sérialisation en lecture du profil client (vu par son propriétaire)."""

    rating = serializers.SerializerMethodField(
        help_text="Note moyenne sur 5 et nombre d'avis reçus, ex : {\"average\": \"4.5\", \"count\": 3}."
    )
    services_list = serializers.SerializerMethodField(
        help_text="Liste des services recherchés sous forme de tableau."
    )
    photo_url = serializers.SerializerMethodField(
        help_text="Adresse de la photo validée, ou null."
    )

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "photo_url",
            "location",
            "services_list",
            "rating",
            "availability_needed",
            "budget",
            "needs_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(RatingSummarySerializer)
    def get_rating(self, obj) -> dict:
        return rating_summary(obj.user)

    def get_services_list(self, obj) -> list[str]:
        return obj.get_services_list()

    def get_photo_url(self, obj) -> str | None:
        return public_photo_url(obj.user)


class ClientProfilePublicSerializer(ClientProfileSerializer):
    """
    Version publique du profil client, vue par les travailleurs.

    Avant un match mutuel, le nom de famille est réduit à son initiale et le
    téléphone n'est jamais inclus. Les besoins (services, budget…) restent visibles.
    """

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["last_name"] = mask_last_name(instance.last_name)
        return data


class ClientProfileWriteSerializer(serializers.ModelSerializer):
    """Sérialisation en écriture — création ou modification du profil client."""

    services_needed = serializers.CharField(
        help_text="Services recherchés séparés par des virgules. Ex : 'nounou,menage'"
    )

    class Meta:
        model = ClientProfile
        fields = [
            "first_name",
            "last_name",
            "location",
            "services_needed",
            "availability_needed",
            "budget",
            "needs_description",
        ]

    def validate_services_needed(self, value: str) -> list[Service]:
        return validate_service_slugs(value)

    def create(self, validated_data):
        # L'utilisateur connecté est lu depuis le contexte fourni par la vue
        user = self.context["request"].user
        services = validated_data.pop("services_needed")
        profile = ClientProfile.objects.create(user=user, **validated_data)
        profile.services_needed.set(services)
        return profile

    def update(self, instance, validated_data):
        services = validated_data.pop("services_needed", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if services is not None:
            instance.services_needed.set(services)
        return instance
