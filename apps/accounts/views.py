"""
Vues (endpoints) de l'app accounts.
Chaque vue correspond à une URL et traite une action précise.
"""
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.http import FileResponse, Http404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import APIException
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.reports.models import warnings_for
from common.schema import AUTH_ERRORS, MESSAGE_ONLY, error, with_message

from . import photos, social
from .models import OTPUnavailableError, SocialAccount, User
from .serializers import (
    SUSPENDED_MESSAGE,
    EmailChangeSerializer,
    EmailLoginSerializer,
    MeSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordChangeSerializer,
    PasswordForgotSerializer,
    PasswordResetSerializer,
    PhotoUploadSerializer,
    RegisterSerializer,
    SocialLoginSerializer,
    UserSerializer,
)


class OTPServiceUnavailable(APIException):
    """Réponse 503 quand l'envoi d'OTP n'est pas disponible (ex : production en V1)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "L'envoi de codes de vérification n'est pas encore disponible."
    default_code = "otp_unavailable"


def _send_otp(user) -> None:
    """Génère l'OTP de l'utilisateur, ou renvoie une erreur 503 si l'envoi est indisponible."""
    try:
        user.generate_otp()
    except OTPUnavailableError:
        raise OTPServiceUnavailable()


def _get_tokens(user) -> dict:
    """Génère une paire de tokens JWT (access + refresh) pour un utilisateur."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


TOKENS = inline_serializer(
    name="Tokens",
    fields={"refresh": drf_serializers.CharField(), "access": drf_serializers.CharField()},
)


def _login_response(user, message: str, status_code=status.HTTP_200_OK) -> Response:
    return Response(
        {"message": message, "tokens": _get_tokens(user), "user": UserSerializer(user).data},
        status=status_code,
    )


class RegisterView(APIView):
    """
    POST /api/accounts/register/

    Crée un nouveau compte utilisateur (client ou travailleur).
    Après l'inscription, l'utilisateur doit valider son numéro via OTP.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Comptes"],
        summary="Créer un compte (client ou travailleur)",
        description="Sans e-mail : un code SMS est envoyé (puis `otp/verify/`). "
        "Avec e-mail + mot de passe : la réponse contient directement les `tokens`.",
        auth=[],
        request=RegisterSerializer,
        responses={
            201: with_message("RegisterResponse", "user", UserSerializer),
            400: error("Numéro invalide ou déjà utilisé, ou rôle invalide."),
            503: error("Envoi des codes SMS indisponible (le compte n'est pas créé)."),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("email"):
            # Inscription avec e-mail + mot de passe : connecté tout de suite, sans code SMS.
            # Le numéro pourra être confirmé plus tard (écran « Sécurité »).
            user = serializer.save()
            return _login_response(user, "Compte créé.", status.HTTP_201_CREATED)
        # Si l'OTP ne peut pas être envoyé, le compte n'est pas créé (annulation complète)
        with transaction.atomic():
            user = serializer.save()
            # On déclenche immédiatement l'envoi de l'OTP après l'inscription
            _send_otp(user)
        return Response(
            {
                "message": "Compte créé. Un code OTP a été envoyé sur votre téléphone.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OTPRequestView(APIView):
    """
    POST /api/accounts/otp/request/

    (Re)envoie un OTP sur le téléphone de l'utilisateur.
    Utile si le code précédent a expiré ou n'a pas été reçu.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Comptes"],
        summary="Recevoir un nouveau code SMS",
        auth=[],
        request=OTPRequestSerializer,
        responses={
            200: MESSAGE_ONLY,
            400: error("Numéro inconnu ou compte suspendu."),
            503: error("Envoi des codes SMS indisponible."),
        },
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        _send_otp(user)
        return Response(
            {"message": "Un nouveau code OTP a été envoyé sur votre téléphone."},
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    """
    POST /api/accounts/otp/verify/

    Vérifie le code OTP et retourne les tokens JWT si correct.
    C'est la seule façon de se connecter en V1.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Comptes"],
        summary="Se connecter avec le code SMS (renvoie les tokens)",
        description="En développement, le code est toujours `123456`. "
        "Copiez `tokens.access` puis cliquez sur **Authorize** en haut de la page.",
        auth=[],
        request=OTPVerifySerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "message": drf_serializers.CharField(),
                    "tokens": TOKENS,
                    "user": UserSerializer(),
                },
            ),
            400: error("Numéro inconnu, compte suspendu ou code invalide."),
        },
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return _login_response(serializer.validated_data["user"], "Connexion réussie.")


class MeView(APIView):
    """
    GET /api/accounts/me/

    Retourne le profil de l'utilisateur connecté, avec les éventuels
    avertissements reçus de l'équipe NOUNOU+.
    Nécessite un token JWT valide dans l'en-tête Authorization.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Comptes"],
        summary="Mon compte (et mes éventuels avertissements)",
        responses={200: MeSerializer, 401: error("Token absent, invalide ou expiré.")},
    )
    def get(self, request):
        data = UserSerializer(request.user).data
        # Avertissements de l'équipe NOUNOU+ (sans jamais révéler qui a signalé)
        data["warnings"] = warnings_for(request.user)
        return Response(data)


def _login_schema(name: str):
    return inline_serializer(
        name=name,
        fields={"message": drf_serializers.CharField(), "tokens": TOKENS, "user": UserSerializer()},
    )


class AuthOptionsView(APIView):
    """
    GET /api/accounts/auth-options/

    Moyens de connexion disponibles sur ce serveur (l'application n'affiche
    actifs que les boutons configurés).
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Comptes"],
        summary="Moyens de connexion disponibles",
        auth=[],
        responses={
            200: inline_serializer(
                name="AuthOptions",
                fields={
                    "sms": drf_serializers.BooleanField(),
                    "google_client_id": drf_serializers.CharField(),
                    "apple_client_id": drf_serializers.CharField(),
                },
            )
        },
    )
    def get(self, request):
        return Response(
            {
                "sms": settings.OTP_MOCK_ENABLED,
                "google_client_id": social.client_id("google"),
                "apple_client_id": social.client_id("apple"),
            }
        )


class EmailLoginView(APIView):
    """POST /api/accounts/login/ — connexion par e-mail + mot de passe."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Comptes"],
        summary="Se connecter avec e-mail + mot de passe",
        auth=[],
        request=EmailLoginSerializer,
        responses={200: _login_schema("EmailLoginResponse"), 400: error("Identifiants incorrects.")},
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return _login_response(serializer.validated_data["user"], "Connexion réussie.")


class PasswordForgotView(APIView):
    """
    POST /api/accounts/password/forgot/

    Envoie un lien de réinitialisation par e-mail. La réponse est toujours la même,
    que l'adresse existe ou non (pour ne pas révéler qui est inscrit).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    MESSAGE = "Si un compte existe avec cette adresse, un e-mail vient d'être envoyé."

    @extend_schema(
        tags=["Comptes"],
        summary="Mot de passe oublié : recevoir un lien par e-mail",
        description="En développement, l'e-mail s'affiche dans la console du serveur Django.",
        auth=[],
        request=PasswordForgotSerializer,
        responses={200: MESSAGE_ONLY},
    )
    def post(self, request):
        serializer = PasswordForgotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email=serializer.validated_data["email"].strip().lower(), is_active=True
        ).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/mot-de-passe/nouveau?uid={uid}&token={token}"
            send_mail(
                subject="NOUNOU+ — nouveau mot de passe",
                message=(
                    "Bonjour,\n\nPour choisir un nouveau mot de passe, ouvrez ce lien "
                    f"(valable 3 jours) :\n{link}\n\n"
                    "Si vous n'avez rien demandé, ignorez simplement cet e-mail.\n\nL'équipe NOUNOU+"
                ),
                from_email=None,
                recipient_list=[user.email],
            )
        return Response({"message": self.MESSAGE})


class PasswordResetView(APIView):
    """POST /api/accounts/password/reset/ — choisir un nouveau mot de passe avec le lien reçu."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Comptes"],
        summary="Mot de passe oublié : choisir le nouveau mot de passe",
        auth=[],
        request=PasswordResetSerializer,
        responses={200: MESSAGE_ONLY, 400: error("Lien invalide ou expiré, ou mot de passe trop faible.")},
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data["uid"])), is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "Ce lien n'est plus valable. Demandez-en un nouveau."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(data["password"], user)
        except DjangoValidationError as exc:
            return Response({"password": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data["password"])
        user.save(update_fields=["password"])
        return Response({"message": "Mot de passe modifié. Vous pouvez vous connecter."})


class PasswordChangeView(APIView):
    """POST /api/accounts/password/change/ — créer ou changer son mot de passe (connecté)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Comptes"],
        summary="Créer ou changer mon mot de passe",
        request=PasswordChangeSerializer,
        responses={200: MESSAGE_ONLY, 400: error("Mot de passe actuel incorrect ou trop faible.")},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"message": "Mot de passe enregistré."})


class EmailChangeView(APIView):
    """POST /api/accounts/email/ — ajouter ou changer son adresse e-mail (connecté)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Comptes"],
        summary="Ajouter ou changer mon e-mail",
        request=EmailChangeSerializer,
        responses={
            200: with_message("EmailChangeResponse", "user", UserSerializer),
            400: error("Adresse déjà utilisée ou mot de passe actuel incorrect."),
        },
    )
    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        request.user.email = serializer.validated_data["email"]
        request.user.save(update_fields=["email"])
        return Response({"message": "Adresse e-mail enregistrée.", "user": UserSerializer(request.user).data})


class SocialNotConfigured(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Cette connexion n'est pas encore activée sur NOUNOU+."
    default_code = "social_not_configured"


class SocialLoginView(APIView):
    """
    POST /api/accounts/social/

    Connexion avec Google ou Apple :
    1. compte déjà lié (ou même e-mail vérifié) → connexion ;
    2. sinon, sans `role` et `phone` → 400 avec `registration_required` : l'application
       demande le rôle et le numéro, puis renvoie le même jeton avec eux → compte créé.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        tags=["Comptes"],
        summary="Se connecter avec Google ou Apple",
        auth=[],
        request=SocialLoginSerializer,
        responses={
            200: _login_schema("SocialLoginResponse"),
            201: _login_schema("SocialRegisterResponse"),
            400: error("Jeton refusé, ou rôle + téléphone nécessaires (`registration_required`)."),
            503: error("Connexion Google / Apple pas encore configurée."),
        },
    )
    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = data["provider"]
        if not social.client_id(provider):
            raise SocialNotConfigured()
        try:
            identity = social.verify_id_token(provider, data["id_token"])
        except social.SocialAuthError:
            return Response(
                {"detail": "La connexion a échoué. Réessayez."}, status=status.HTTP_400_BAD_REQUEST
            )

        link = SocialAccount.objects.filter(provider=provider, uid=identity.uid).select_related("user").first()
        user = link.user if link else None
        if user is None and identity.email:
            # Même adresse e-mail confirmée par Google/Apple : on relie au compte existant
            user = User.objects.filter(email=identity.email).first()
            if user is not None:
                SocialAccount.objects.create(user=user, provider=provider, uid=identity.uid)
        if user is not None:
            if not user.is_active:
                return Response({"detail": SUSPENDED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
            return _login_response(user, "Connexion réussie.")

        if not data.get("role") or not data.get("phone"):
            return Response(
                {
                    "detail": "Dernière étape : choisissez votre profil et indiquez votre numéro.",
                    "registration_required": True,
                    "email": identity.email,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            user = User.objects.create_user(phone=data["phone"], role=data["role"], email=identity.email)
            SocialAccount.objects.create(user=user, provider=provider, uid=identity.uid)
        return _login_response(user, "Compte créé.", status.HTTP_201_CREATED)


class MyPhotoView(APIView):
    """
    GET    /api/accounts/photo/ → ma photo (même en attente de validation)
    POST   /api/accounts/photo/ → envoyer / remplacer ma photo (multipart, champ `photo`)
    DELETE /api/accounts/photo/ → supprimer ma photo
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        tags=["Photos"],
        summary="Voir ma photo de profil (fichier JPEG)",
        responses={(200, "image/jpeg"): bytes, 404: error("Pas de photo."), **AUTH_ERRORS},
    )
    def get(self, request):
        if not request.user.photo:
            raise Http404
        return FileResponse(request.user.photo.open("rb"), content_type="image/jpeg")

    @extend_schema(
        tags=["Photos"],
        summary="Envoyer ma photo de profil",
        description="JPG, PNG ou WEBP, 5 Mo maximum. La photo est réduite et nettoyée "
        "(position GPS supprimée), puis montrée aux autres après validation par l'équipe.",
        request={"multipart/form-data": PhotoUploadSerializer},
        responses={
            200: with_message("PhotoReceived", "user", UserSerializer),
            400: error("Fichier absent, trop lourd ou qui n'est pas une image."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            photos.set_photo(request.user, serializer.validated_data["photo"])
        except photos.InvalidPhoto as exc:
            return Response({"photo": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Photo reçue. Elle sera visible après validation par l'équipe NOUNOU+.",
                "user": UserSerializer(request.user).data,
            }
        )

    @extend_schema(tags=["Photos"], summary="Supprimer ma photo", responses={200: MESSAGE_ONLY, **AUTH_ERRORS})
    def delete(self, request):
        photos.delete_photo(request.user)
        return Response({"message": "Photo supprimée."})


class PublicPhotoView(APIView):
    """
    GET /api/photos/<nom>

    Photo validée d'un profil (adresse donnée par `photo_url` dans les profils).
    Une photo en attente ou refusée n'est jamais servie ici.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Photos"],
        summary="Photo de profil validée",
        auth=[],
        responses={(200, "image/jpeg"): bytes, 404: error("Photo introuvable ou pas encore validée.")},
    )
    def get(self, request, name):
        user = User.objects.filter(photo=f"photos/{name}", photo_status=User.PHOTO_APPROVED).first()
        if user is None:
            raise Http404
        response = FileResponse(user.photo.open("rb"), content_type="image/jpeg")
        response["Cache-Control"] = "public, max-age=86400"
        return response
