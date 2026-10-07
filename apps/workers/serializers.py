"""
Serializers de l'app workers.

- WorkerProfileSerializer    : lecture (liste publique et détail)
- WorkerProfileWriteSerializer : écriture (création et modification)
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from apps.accounts.photos import public_photo_url
from apps.services.models import Service
from apps.reviews.models import rating_summary
from apps.reviews.serializers import RatingSummarySerializer
from apps.services.serializers import validate_service_slugs
from common.privacy import mask_last_name

from .models import WorkerProfile


class TrustSerializer(serializers.Serializer):
    phone = serializers.BooleanField()
    identity = serializers.BooleanField()
    references = serializers.BooleanField()


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
    rating = serializers.SerializerMethodField(
        help_text="Note moyenne sur 5 et nombre d'avis reçus, ex : {\"average\": \"4.5\", \"count\": 3}."
    )
    phone_display = serializers.SerializerMethodField(
        help_text="Numéro masqué (ex: +243 8** *** **8) — complet uniquement après match."
    )
    photo_url = serializers.SerializerMethodField(help_text="Adresse de la photo validée, ou null.")
    trust = serializers.SerializerMethodField(
        help_text="Contrôles faits par NOUNOU+ : téléphone confirmé par SMS, identité validée, "
        "au moins une référence vérifiée. Ce n'est pas une garantie d'absence de risque."
    )

    class Meta:
        model = WorkerProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "photo_url",
            "bio",
            "services",
            "services_list",
            "years_experience",
            "availability",
            "expected_salary",
            "location",
            "is_verified",
            "trust",
            "rating",
            "phone_display",
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

    @extend_schema_field(TrustSerializer)
    def get_trust(self, obj) -> dict:
        return {
            "phone": obj.user.phone_verified,
            "identity": obj.is_verified,
            "references": obj.references.filter(status="verifiee").exists(),
        }

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
