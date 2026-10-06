"""
Serializers de l'app workers.

- WorkerProfileSerializer    : lecture (liste publique et détail)
- WorkerProfileWriteSerializer : écriture (création et modification)
"""
from rest_framework import serializers
from apps.services.models import Service
from apps.services.serializers import validate_service_slugs
from common.privacy import mask_last_name

from .models import WorkerProfile


class WorkerProfileSerializer(serializers.ModelSerializer):
    """
    Sérialisation en lecture d'un profil travailleur.
    Utilisé pour la liste publique et le détail (profil propre).

    Note : le numéro de téléphone complet n'est PAS exposé ici —
    il le sera uniquement après un match mutuel (règle brief §contraintes).
    """

    services_list = serializers.SerializerMethodField(
        help_text="Liste des services sous forme de tableau."
    )
    phone_display = serializers.SerializerMethodField(
        help_text="Numéro masqué (ex: +243 8** *** **8) — complet uniquement après match."
    )

    class Meta:
        model = WorkerProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "bio",
            "services",
            "services_list",
            "years_experience",
            "availability",
            "expected_salary",
            "location",
            "is_verified",
            "phone_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_services_list(self, obj) -> list[str]:
        return obj.get_services_list()

    def get_phone_display(self, obj) -> str:
        """Masque le numéro de téléphone avant un match mutuel."""
        phone = str(obj.user.phone)
        # Garde les 4 premiers et le dernier caractère, remplace le reste par *
        if len(phone) > 6:
            return phone[:5] + "*" * (len(phone) - 6) + phone[-1]
        return "****"


class WorkerProfilePublicSerializer(WorkerProfileSerializer):
    """
    Version publique du profil, utilisée dans la liste vue par les autres utilisateurs.

    Avant un match mutuel, le nom de famille est réduit à son initiale
    (ex : "Mutombo" → "M.") afin de ne pas exposer l'identité complète
    (règle brief §contraintes). Le travailleur voit son propre nom complet
    via /api/workers/profile/me/.
    """

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["last_name"] = mask_last_name(instance.last_name)
        return data


class WorkerProfileWriteSerializer(serializers.ModelSerializer):
    """
    Sérialisation en écriture — utilisé pour créer ou modifier un profil.
    `is_verified` est explicitement exclu : seul l'admin peut le modifier.
    """

    services = serializers.CharField(
        help_text="Services séparés par des virgules. Ex : 'nounou,cuisine'"
    )

    class Meta:
        model = WorkerProfile
        fields = [
            "first_name",
            "last_name",
            "bio",
            "services",
            "years_experience",
            "availability",
            "expected_salary",
            "location",
        ]

    def validate_services(self, value: str) -> list[Service]:
        return validate_service_slugs(value)

    def create(self, validated_data):
        # L'utilisateur connecté est lu depuis le contexte fourni par la vue
        user = self.context["request"].user
        services = validated_data.pop("services")
        profile = WorkerProfile.objects.create(user=user, **validated_data)
        profile.services.set(services)
        return profile

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if services is not None:
            instance.services.set(services)
        return instance
