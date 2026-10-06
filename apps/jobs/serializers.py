"""
Serializers de l'app jobs.

- JobRequestSerializer       : annonce vue par la famille qui l'a publiée
- JobRequestPublicSerializer : annonce vue par les travailleurs (famille présentée
                               par prénom + initiale, jamais de téléphone)
- JobRequestWriteSerializer  : création / modification par la famille
"""
from rest_framework import serializers

from apps.accounts.photos import public_photo_url
from apps.reviews.models import rating_summary
from apps.services.models import Service
from apps.services.serializers import ServiceSerializer
from common.privacy import mask_last_name

from .models import JobRequest

JOB_FIELDS = [
    "id",
    "title",
    "service",
    "availability",
    "budget",
    "location",
    "description",
    "status",
    "created_at",
    "updated_at",
]


class JobRequestSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    interested_workers = serializers.SerializerMethodField(
        help_text="Nombre de travailleurs ayant répondu à cette annonce."
    )

    class Meta:
        model = JobRequest
        fields = JOB_FIELDS + ["interested_workers"]
        read_only_fields = fields

    def get_interested_workers(self, obj) -> int:
        return obj.matches.count()


class JobRequestPublicSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    client = serializers.SerializerMethodField(
        help_text="La famille : identifiant de profil, prénom + initiale, note moyenne."
    )

    class Meta:
        model = JobRequest
        fields = JOB_FIELDS + ["client"]
        read_only_fields = fields

    def get_client(self, obj) -> dict:
        client = obj.client
        return {
            "profile_id": client.id,
            "name": f"{client.first_name} {mask_last_name(client.last_name)}".strip(),
            "photo_url": public_photo_url(client.user),
            "rating": rating_summary(client.user),
        }


class JobRequestWriteSerializer(serializers.ModelSerializer):
    service = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Service.objects.all(),
        help_text="Service demandé : nounou, menage ou cuisine.",
    )
    location = serializers.CharField(
        max_length=200, required=False, allow_blank=True,
        help_text="Facultatif : par défaut, le quartier du profil client.",
    )

    class Meta:
        model = JobRequest
        fields = ["title", "service", "availability", "budget", "location", "description", "status"]
        extra_kwargs = {"status": {"required": False}}

    def validate(self, attrs):
        if self.instance is None and attrs.get("status", JobRequest.STATUS_OPEN) != JobRequest.STATUS_OPEN:
            raise serializers.ValidationError({"status": "Une nouvelle annonce est toujours ouverte."})
        return attrs

    def create(self, validated_data):
        client = self.context["client"]
        if not validated_data.get("location"):
            validated_data["location"] = client.location
        return JobRequest.objects.create(client=client, **validated_data)

    def update(self, instance, validated_data):
        if "location" in validated_data and not validated_data["location"]:
            validated_data["location"] = instance.client.location
        return super().update(instance, validated_data)
