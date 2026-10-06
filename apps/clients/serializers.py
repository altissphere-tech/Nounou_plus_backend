"""
Serializers de l'app clients.

- ClientProfileSerializer      : lecture (son propre profil)
- ClientProfileWriteSerializer : écriture (création et modification)
"""
from rest_framework import serializers

from apps.services.models import Service
from apps.services.serializers import validate_service_slugs

from .models import ClientProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    """Sérialisation en lecture du profil client (vu par son propriétaire)."""

    services_list = serializers.SerializerMethodField(
        help_text="Liste des services recherchés sous forme de tableau."
    )

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "location",
            "services_list",
            "availability_needed",
            "budget",
            "needs_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_services_list(self, obj) -> list[str]:
        return obj.get_services_list()


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
