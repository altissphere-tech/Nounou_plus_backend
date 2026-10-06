"""
Serializers de l'app workers.

- WorkerProfileSerializer    : lecture (liste publique et détail)
- WorkerProfileWriteSerializer : écriture (création et modification)
"""
from rest_framework import serializers
from .models import WorkerProfile

VALID_SERVICES = {
    WorkerProfile.SERVICE_NOUNOU,
    WorkerProfile.SERVICE_MENAGE,
    WorkerProfile.SERVICE_CUISINE,
}


def _validate_services(value: str) -> str:
    """
    Valide la chaîne de services.
    Ex : "nounou,cuisine" → valide
         "nounou,invalide" → lève une ValidationError
    """
    items = [s.strip() for s in value.split(",") if s.strip()]
    if not items:
        raise serializers.ValidationError("Au moins un service doit être renseigné.")
    invalid = set(items) - VALID_SERVICES
    if invalid:
        raise serializers.ValidationError(
            f"Service(s) invalide(s) : {', '.join(invalid)}. "
            f"Valeurs acceptées : {', '.join(VALID_SERVICES)}."
        )
    # Normalise : dédoublonne et trie
    return ",".join(sorted(set(items)))


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

    def validate_services(self, value: str) -> str:
        return _validate_services(value)

    def create(self, validated_data):
        # L'utilisateur est injecté depuis la vue via `save(user=request.user)`
        user = self.context["request"].user
        return WorkerProfile.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
