"""
Serializers de l'app services.

- ServiceSerializer       : lecture du catalogue (liste des services)
- validate_service_slugs  : convertit "nounou,cuisine" en objets Service,
                            utilisé par les profils travailleurs et clients
"""
from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["slug", "label"]
        read_only_fields = fields


def validate_service_slugs(value: str) -> list[Service]:
    """
    Valide la chaîne de services et la convertit en objets Service du catalogue.
    Ex : "nounou,cuisine" → [<Service cuisine>, <Service nounou>]
         "nounou,invalide" → lève une ValidationError
    """
    slugs = {s.strip() for s in value.split(",") if s.strip()}
    if not slugs:
        raise serializers.ValidationError("Au moins un service doit être renseigné.")
    services = list(Service.objects.filter(slug__in=slugs))
    invalid = slugs - {service.slug for service in services}
    if invalid:
        accepted = Service.objects.values_list("slug", flat=True)
        raise serializers.ValidationError(
            f"Service(s) invalide(s) : {', '.join(sorted(invalid))}. "
            f"Valeurs acceptées : {', '.join(accepted)}."
        )
    return services
