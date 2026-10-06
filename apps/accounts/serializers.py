"""
Serializers de l'app accounts.

Un serializer transforme les données JSON envoyées par le client
en objets Python valides (et inversement).
"""
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import User

SUSPENDED_MESSAGE = "Ce compte a été suspendu. Contactez l'équipe NOUNOU+ pour plus d'informations."


class RegisterSerializer(serializers.Serializer):
    """
    Inscription d'un nouvel utilisateur.
    Champs requis : numéro de téléphone + rôle.
    """

    phone = PhoneNumberField(
        help_text="Format E.164 recommandé, ex : +243812345678"
    )
    role = serializers.ChoiceField(
        choices=[User.ROLE_CLIENT, User.ROLE_WORKER],
        help_text="'client' ou 'travailleur' (l'admin ne peut pas s'inscrire via l'API)",
    )

    def validate_phone(self, value):
        """Vérifie qu'aucun compte n'existe déjà avec ce numéro."""
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Un compte existe déjà avec ce numéro de téléphone."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            phone=validated_data["phone"],
            role=validated_data["role"],
        )


class OTPRequestSerializer(serializers.Serializer):
    """
    Demande d'envoi d'un OTP sur un numéro de téléphone existant.
    """

    phone = PhoneNumberField()

    def validate_phone(self, value):
        try:
            self._user = User.objects.get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Aucun compte trouvé avec ce numéro.")
        if not self._user.is_active:
            raise serializers.ValidationError(SUSPENDED_MESSAGE)
        return value

    def get_user(self) -> User:
        return self._user


class OTPVerifySerializer(serializers.Serializer):
    """
    Vérification de l'OTP : si correct, retourne les tokens JWT.
    """

    phone = PhoneNumberField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        phone = attrs["phone"]
        code = attrs["code"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "Aucun compte trouvé avec ce numéro."})

        if not user.is_active:
            raise serializers.ValidationError({"phone": SUSPENDED_MESSAGE})

        if not user.verify_otp(code):
            raise serializers.ValidationError({"code": "Code OTP invalide ou expiré."})

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Représentation publique d'un utilisateur (sans données sensibles)."""

    class Meta:
        model = User
        fields = ["id", "phone", "role", "phone_verified", "created_at"]
        read_only_fields = fields
