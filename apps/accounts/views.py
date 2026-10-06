"""
Vues (endpoints) de l'app accounts.
Chaque vue correspond à une URL et traite une action précise.
"""
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPUnavailableError
from .serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    RegisterSerializer,
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


class RegisterView(APIView):
    """
    POST /api/accounts/register/

    Crée un nouveau compte utilisateur (client ou travailleur).
    Après l'inscription, l'utilisateur doit valider son numéro via OTP.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = _get_tokens(user)
        return Response(
            {
                "message": "Connexion réussie.",
                "tokens": tokens,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/accounts/me/

    Retourne le profil de l'utilisateur connecté.
    Nécessite un token JWT valide dans l'en-tête Authorization.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
