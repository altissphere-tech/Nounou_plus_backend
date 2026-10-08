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


REAUTH_MESSAGE = "Pour votre sécurité, reconnectez-vous puis recommencez."
PHONE_UNVERIFIED_MESSAGE = "Confirmez d'abord votre numéro avec le code reçu par SMS."


class RegisterSerializer(serializers.Serializer):
    """
    Inscription d'un nouvel utilisateur : numéro de téléphone + rôle.
    Le compte n'est utilisable qu'après le code SMS (preuve que le numéro est le sien).
    L'e-mail et le mot de passe s'ajoutent ensuite, une fois connecté (écran « Sécurité »).
    """

    phone = PhoneNumberField(
        help_text="Format E.164 recommandé, ex : +243812345678"
    )
    role = serializers.ChoiceField(
        choices=[User.ROLE_CLIENT, User.ROLE_WORKER],
        help_text="'client' ou 'travailleur' (l'admin ne peut pas s'inscrire via l'API)",
    )

    def create(self, validated_data):
        return User.objects.create_user(phone=validated_data["phone"], role=validated_data["role"])


class OTPRequestSerializer(serializers.Serializer):
    """
    Demande d'envoi d'un OTP sur un numéro de téléphone existant.
    """

    phone = PhoneNumberField()

    def get_user(self) -> User | None:
        """
        Le compte de ce numéro, ou None : la réponse reste la même (pas d'indice).
        Un compte suspendu reçoit aussi un code ; la suspension n'est annoncée
        qu'après un code correct, donc seulement au titulaire du numéro.
        """
        return User.objects.filter(phone=self.validated_data["phone"]).first()


class OTPVerifySerializer(serializers.Serializer):
    """
    Vérification de l'OTP : si correct, retourne les tokens JWT.
    """

    phone = PhoneNumberField()
    code = serializers.CharField(max_length=6, min_length=6)
    social_ticket = serializers.CharField(
        required=False,
        help_text="Renvoyé par `social/` : relie le compte Google / Apple une fois le numéro confirmé.",
    )

    def validate(self, attrs):
        phone = attrs["phone"]
        code = attrs["code"]

        user = User.objects.filter(phone=phone).first()
        attrs["first_verification"] = user is not None and not user.phone_verified
        # Même réponse pour un numéro inconnu et un mauvais code (pas d'indice)
        if user is None or not user.verify_otp(code):
            raise serializers.ValidationError({"code": "Code OTP invalide ou expiré."})
        if not user.is_active:
            raise serializers.ValidationError({"phone": SUSPENDED_MESSAGE})

        attrs["user"] = user
        return attrs


class EmailLoginSerializer(serializers.Serializer):
    """Connexion par e-mail + mot de passe."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        # Seule une adresse confirmée permet de se connecter
        user = User.objects.filter(email=attrs["email"].strip().lower()).first()
        if user is None:
            # Même durée de calcul qu'un vrai compte : le temps de réponse ne révèle rien
            User().set_password(attrs["password"])
            raise serializers.ValidationError("E-mail ou mot de passe incorrect.")
        # Même message dans tous les cas : on ne révèle pas si l'adresse existe
        if not user.check_password(attrs["password"]):
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


def check_identity(context, attrs) -> None:
    """
    Avant de changer le mot de passe ou l'e-mail : le mot de passe actuel s'il existe,
    sinon une connexion récente (code SMS ou Google / Apple de moins de 10 minutes).
    Un jeton volé ne suffit donc pas à s'approprier le compte.
    """
    user = context["user"]
    if user.has_usable_password():
        if not user.check_password(attrs.get("current_password", "")):
            raise serializers.ValidationError({"current_password": "Mot de passe actuel incorrect."})
    elif not context.get("recent_login"):
        raise serializers.ValidationError({"detail": REAUTH_MESSAGE, "reauth_required": True})


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=False,
        write_only=True,
        help_text="Obligatoire si le compte a déjà un mot de passe.",
    )
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        check_identity(self.context, attrs)
        validate_password(attrs["new_password"], self.context["user"])
        return attrs


class EmailChangeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    current_password = serializers.CharField(
        required=False,
        write_only=True,
        help_text="Obligatoire si le compte a déjà un mot de passe.",
    )

    def validate(self, attrs):
        check_identity(self.context, attrs)
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
            "email_verified",
            "pending_email",
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


class EmailConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Valeur `token` du lien reçu par e-mail.")
