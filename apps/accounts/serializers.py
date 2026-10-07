"""
Serializers de l'app accounts.

Un serializer transforme les données JSON envoyées par le client
en objets Python valides (et inversement).
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import SocialAccount, User

SUSPENDED_MESSAGE = "Ce compte a été suspendu. Contactez l'équipe NOUNOU+ pour plus d'informations."


def validate_new_email(value: str, user: User | None = None) -> str:
    """Adresse e-mail en minuscules, refusée si un autre compte l'utilise déjà."""
    value = value.strip().lower()
    others = User.objects.filter(email=value)
    if user is not None:
        others = others.exclude(pk=user.pk)
    if others.exists():
        raise serializers.ValidationError("Un compte existe déjà avec cette adresse e-mail.")
    return value


class RegisterSerializer(serializers.Serializer):
    """
    Inscription d'un nouvel utilisateur.
    Champs requis : numéro de téléphone + rôle.
    Facultatif : e-mail + mot de passe (connexion sans code SMS ensuite).
    """

    phone = PhoneNumberField(
        help_text="Format E.164 recommandé, ex : +243812345678"
    )
    role = serializers.ChoiceField(
        choices=[User.ROLE_CLIENT, User.ROLE_WORKER],
        help_text="'client' ou 'travailleur' (l'admin ne peut pas s'inscrire via l'API)",
    )
    email = serializers.EmailField(required=False, help_text="Facultatif, avec `password`.")
    password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="Au moins 8 caractères. Obligatoire si un e-mail est donné.",
    )

    def validate_phone(self, value):
        """Vérifie qu'aucun compte n'existe déjà avec ce numéro."""
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Un compte existe déjà avec ce numéro de téléphone."
            )
        return value

    def validate_email(self, value):
        return validate_new_email(value)

    def validate(self, attrs):
        if bool(attrs.get("email")) != bool(attrs.get("password")):
            raise serializers.ValidationError(
                "L'e-mail et le mot de passe vont ensemble : donnez les deux, ou aucun."
            )
        if attrs.get("password"):
            validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            phone=validated_data["phone"],
            role=validated_data["role"],
            email=validated_data.get("email"),
            password=validated_data.get("password"),
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


class EmailLoginSerializer(serializers.Serializer):
    """Connexion par e-mail + mot de passe."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"].strip().lower()).first()
        # Même message dans tous les cas : on ne révèle pas si l'adresse existe
        if user is None or not user.check_password(attrs["password"]):
            raise serializers.ValidationError("E-mail ou mot de passe incorrect.")
        if not user.is_active:
            raise serializers.ValidationError(SUSPENDED_MESSAGE)
        attrs["user"] = user
        return attrs


class PasswordForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    uid = serializers.CharField(help_text="Valeur `uid` du lien reçu par e-mail.")
    token = serializers.CharField(help_text="Valeur `token` du lien reçu par e-mail.")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=False,
        write_only=True,
        help_text="Obligatoire si le compte a déjà un mot de passe.",
    )
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["user"]
        if user.has_usable_password() and not user.check_password(attrs.get("current_password", "")):
            raise serializers.ValidationError({"current_password": "Mot de passe actuel incorrect."})
        validate_password(attrs["new_password"], user)
        return attrs


class EmailChangeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    current_password = serializers.CharField(
        required=False,
        write_only=True,
        help_text="Obligatoire si le compte a déjà un mot de passe.",
    )

    def validate_email(self, value):
        return validate_new_email(value, self.context["user"])

    def validate(self, attrs):
        user = self.context["user"]
        if user.has_usable_password() and not user.check_password(attrs.get("current_password", "")):
            raise serializers.ValidationError({"current_password": "Mot de passe actuel incorrect."})
        return attrs


class SocialLoginSerializer(serializers.Serializer):
    """
    Connexion Google / Apple. Pour un nouveau compte, la première réponse demande
    le rôle et le numéro de téléphone ; l'application renvoie alors le même jeton avec eux.
    """

    provider = serializers.ChoiceField(choices=[c[0] for c in SocialAccount.PROVIDER_CHOICES])
    id_token = serializers.CharField(help_text="Jeton d'identité fourni par Google ou Apple.")
    role = serializers.ChoiceField(choices=[User.ROLE_CLIENT, User.ROLE_WORKER], required=False)
    phone = PhoneNumberField(required=False)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Un compte existe déjà avec ce numéro : connectez-vous avec le code SMS, "
                "puis liez votre e-mail dans « Sécurité »."
            )
        return value


class PhotoUploadSerializer(serializers.Serializer):
    photo = serializers.FileField(help_text="Image JPG, PNG ou WEBP, 5 Mo maximum.")


class UserSerializer(serializers.ModelSerializer):
    """Représentation d'un utilisateur pour lui-même (sans données sensibles)."""

    has_password = serializers.SerializerMethodField()
    social_providers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "role",
            "phone_verified",
            "email",
            "has_password",
            "social_providers",
            "photo_status",
            "photo_rejection_reason",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_password(self, obj) -> bool:
        return obj.has_usable_password()

    def get_social_providers(self, obj) -> list[str]:
        return list(obj.social_accounts.values_list("provider", flat=True))


class WarningSerializer(serializers.Serializer):
    message = serializers.CharField()
    date = serializers.DateTimeField()


class MeSerializer(UserSerializer):
    """Format de /api/accounts/me/ : le compte + les avertissements de l'équipe NOUNOU+."""

    warnings = WarningSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["warnings"]
        read_only_fields = fields
