"""
Vues (endpoints) de l'app accounts.
Chaque vue correspond à une URL et traite une action précise.
"""
from collections.abc import Mapping

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.http import FileResponse, Http404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.reports.models import warnings_for
from common import security_log
from common.authentication import recent_login, tokens_for
from common.schema import AUTH_ERRORS, MESSAGE_ONLY, error, with_message
from common.throttles import (
    LoginEmailThrottle,
    OtpVerifyPhoneThrottle,
    SmsPhoneThrottle,
    check_sms_send,
    throttle,
)

from . import emails, photos, sms, social
from .models import OTPUnavailableError, SocialAccount, User
from .serializers import (
    PHONE_UNVERIFIED_MESSAGE,
    SUSPENDED_MESSAGE,
    EmailChangeSerializer,
    EmailConfirmSerializer,
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


def _send_otp(user, request=None) -> None:
    """
    Génère l'OTP de l'utilisateur, ou renvoie une erreur 503 si l'envoi est indisponible.
    Avec `request`, vérifie d'abord les limites d'envoi par numéro et par appareil ; sans,
    l'appelant les a déjà vérifiées (avant de savoir si le numéro est inscrit).
    """
    if request is not None:
        check_sms_send(request, user.phone)
    try:
        user.generate_otp()
    except OTPUnavailableError:
        raise OTPServiceUnavailable()


def _field(request, name: str):
    """Valeur d'un champ envoyé, ou None si le corps n'est pas un objet JSON (ex : une liste)."""
    return request.data.get(name) if isinstance(request.data, Mapping) else None


def _require_sms() -> None:
    """Vérifié avant toute recherche de compte : la réponse ne dépend pas du numéro."""
    if not sms.available():
        raise OTPServiceUnavailable()


def _phone_verification_response(user, request, extra: dict | None = None) -> Response:
    """Le numéro du compte n'est pas encore confirmé : un code lui est envoyé."""
    _send_otp(user, request)
    return Response(
        {
            "detail": PHONE_UNVERIFIED_MESSAGE,
            "phone_verification_required": True,
            "phone": str(user.phone),
            **(extra or {}),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _reclaim_phone(user, request) -> None:
    """
    Première confirmation du numéro par code SMS : la personne qui reçoit les SMS de ce
    numéro en est la titulaire. Si quelqu'un avait attaché au compte un mot de passe,
    un e-mail ou un compte Google / Apple sans jamais confirmer le numéro, ces accès
    sont retirés et ses sessions fermées : il ne peut pas « squatter » le numéro.
    """
    had_access = user.has_usable_password() or user.email or user.pending_email or user.social_accounts.exists()
    if not had_access:
        return
    user.set_unusable_password()
    user.email = None
    user.email_verified = False
    user.pending_email = ""
    user.save(update_fields=["password", "email", "email_verified", "pending_email"])
    user.social_accounts.all().delete()
    user.end_all_sessions()
    security_log.event("numero_recupere", request, compte=user.pk)


SOCIAL_TICKET_SALT = "nounou.social-ticket"
SOCIAL_TICKET_MAX_AGE = 15 * 60


def _get_tokens(user) -> dict:
    """Génère une paire de tokens JWT (access + refresh) pour un utilisateur."""
    refresh = tokens_for(user)
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


def _login_schema(name: str):
    return inline_serializer(
        name=name,
        fields={"message": drf_serializers.CharField(), "tokens": TOKENS, "user": UserSerializer()},
    )


REGISTER_SMS_MESSAGE = "Un code de vérification a été envoyé par SMS."
OTP_SENT_MESSAGE = "Si ce numéro est inscrit sur NOUNOU+, un code vient d'être envoyé par SMS."


class RegisterView(APIView):
    """
    POST /api/accounts/register/

    Crée un nouveau compte utilisateur (client ou travailleur).
    Après l'inscription, l'utilisateur doit valider son numéro via OTP.
    """

    permission_classes = [AllowAny]
    throttle_classes = [throttle("register"), throttle("sms_ip"), SmsPhoneThrottle]

    @extend_schema(
        tags=["Comptes"],
        summary="Créer un compte (client ou travailleur)",
        description="Un code SMS est envoyé (puis `otp/verify/`). Si le numéro est déjà inscrit, "
        "la réponse est identique et le titulaire reçoit un code de connexion. L'e-mail et le "
        "mot de passe s'ajoutent ensuite, une fois connecté (`email/`, `password/change/`).",
        auth=[],
        request=RegisterSerializer,
        responses={
            201: MESSAGE_ONLY,
            400: error("Numéro ou rôle invalide."),
            503: error("Envoi des codes SMS indisponible (le compte n'est pas créé)."),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _require_sms()
        phone = serializer.validated_data["phone"]
        with transaction.atomic():
            existing = User.objects.select_for_update().filter(phone=phone).first()
            if existing is None:
                user = serializer.save()
            else:
                # Numéro déjà inscrit : même réponse (on ne révèle pas qui est inscrit) ; le
                # titulaire reçoit un code. Un compte jamais confirmé ne contient rien : il
                # prend le rôle demandé, au cas où quelqu'un aurait inscrit ce numéro avant.
                user = existing
                if not existing.phone_verified and existing.role != serializer.validated_data["role"]:
                    existing.role = serializer.validated_data["role"]
                    existing.save(update_fields=["role"])
            _send_otp(user, request)
        return Response({"message": REGISTER_SMS_MESSAGE}, status=status.HTTP_201_CREATED)


class OTPRequestView(APIView):
    """
    POST /api/accounts/otp/request/

    (Re)envoie un OTP sur le téléphone de l'utilisateur.
    Utile si le code précédent a expiré ou n'a pas été reçu.
    """

    permission_classes = [AllowAny]
    throttle_classes = [throttle("sms_ip"), SmsPhoneThrottle]

    @extend_schema(
        tags=["Comptes"],
        summary="Recevoir un nouveau code SMS",
        auth=[],
        request=OTPRequestSerializer,
        responses={
            200: MESSAGE_ONLY,
            400: error("Numéro mal écrit."),
            503: error("Envoi des codes SMS indisponible."),
        },
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _require_sms()
        # Compté même pour un numéro inconnu : la limite ne révèle pas qui est inscrit
        check_sms_send(request, serializer.validated_data["phone"])
        user = serializer.get_user()
        if user is not None:
            _send_otp(user)
        return Response({"message": OTP_SENT_MESSAGE}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    """
    POST /api/accounts/otp/verify/

    Vérifie le code OTP et retourne les tokens JWT si correct.
    C'est la seule façon de se connecter en V1.
    """

    permission_classes = [AllowAny]
    throttle_classes = [throttle("otp_verify_ip"), OtpVerifyPhoneThrottle]

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
            400: error("Code invalide (ou numéro inconnu : même réponse), ou compte suspendu."),
        },
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            security_log.event("code_sms_refuse", request, numero=security_log.fingerprint(_field(request, "phone")))
            raise ValidationError(serializer.errors)
        user = serializer.validated_data["user"]
        if serializer.validated_data.get("first_verification"):
            _reclaim_phone(user, request)
        ticket = serializer.validated_data.get("social_ticket")
        if ticket:
            _link_social_ticket(user, ticket, request)
        security_log.event("connexion", request, compte=user.pk, methode="sms")
        return _login_response(user, "Connexion réussie.")


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
    throttle_classes = [throttle("auth"), LoginEmailThrottle]

    @extend_schema(
        tags=["Comptes"],
        summary="Se connecter avec e-mail + mot de passe",
        auth=[],
        request=EmailLoginSerializer,
        responses={200: _login_schema("EmailLoginResponse"), 400: error("Identifiants incorrects.")},
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if not serializer.is_valid():
            security_log.event("connexion_refusee", request, email=security_log.fingerprint(_field(request, "email")))
            raise ValidationError(serializer.errors)
        user = serializer.validated_data["user"]
        if not user.phone_verified:
            return _phone_verification_response(user, request)
        security_log.event("connexion", request, compte=user.pk, methode="email")
        return _login_response(user, "Connexion réussie.")


class PasswordForgotView(APIView):
    """
    POST /api/accounts/password/forgot/

    Envoie un lien de réinitialisation par e-mail. La réponse est toujours la même,
    que l'adresse existe ou non (pour ne pas révéler qui est inscrit).
    """

    permission_classes = [AllowAny]
    throttle_classes = [throttle("auth"), LoginEmailThrottle]
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
        # Seule une adresse vérifiée reçoit le lien (sinon : prise de contrôle possible)
        user = User.objects.filter(
            email=serializer.validated_data["email"].strip().lower(), is_active=True
        ).first()
        security_log.event(
            "mot_de_passe_oublie", request, email=security_log.fingerprint(serializer.validated_data["email"]),
            compte=user.pk if user else "-",
        )
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
    throttle_classes = [throttle("auth")]

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
        user.end_all_sessions()  # un éventuel voleur de session est déconnecté
        security_log.event("mot_de_passe_reinitialise", request, compte=user.pk)
        return Response({"message": "Mot de passe modifié. Vous pouvez vous connecter."})


class PasswordChangeView(APIView):
    """POST /api/accounts/password/change/ — créer ou changer son mot de passe (connecté)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Comptes"],
        summary="Créer ou changer mon mot de passe",
        description="Déconnecte les autres appareils. La réponse contient de nouveaux `tokens`.",
        request=PasswordChangeSerializer,
        responses={
            200: _login_schema("PasswordChangeResponse"),
            400: error("Mot de passe actuel incorrect ou trop faible."),
        },
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"user": request.user, "recent_login": recent_login(request)}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        # Les autres appareils sont déconnectés ; celui-ci reçoit de nouveaux jetons
        request.user.end_all_sessions()
        security_log.event("mot_de_passe_change", request, compte=request.user.pk)
        return _login_response(request.user, "Mot de passe enregistré. Vos autres appareils sont déconnectés.")


class EmailChangeView(APIView):
    """POST /api/accounts/email/ — ajouter ou changer son adresse e-mail (connecté)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle("email_send")]

    @extend_schema(
        tags=["Comptes"],
        summary="Ajouter ou changer mon e-mail",
        request=EmailChangeSerializer,
        responses={
            200: with_message("EmailChangeResponse", "user", UserSerializer),
            400: error("Mot de passe actuel incorrect, ou connexion trop ancienne (`reauth_required`)."),
        },
    )
    def post(self, request):
        serializer = EmailChangeSerializer(
            data=request.data, context={"user": request.user, "recent_login": recent_login(request)}
        )
        serializer.is_valid(raise_exception=True)
        # L'adresse reste « en attente » jusqu'au clic sur le lien (même réponse si elle
        # appartient déjà à un autre compte : son titulaire est seulement prévenu)
        emails.request_email(request.user, serializer.validated_data["email"])
        security_log.event("email_change", request, compte=request.user.pk)
        return Response(
            {
                "message": "Adresse e-mail enregistrée. Confirmez-la avec le lien reçu par e-mail.",
                "user": UserSerializer(request.user).data,
            }
        )


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
    throttle_classes = [throttle("auth")]

    @extend_schema(
        tags=["Comptes"],
        summary="Se connecter avec Google ou Apple",
        auth=[],
        request=SocialLoginSerializer,
        responses={
            200: _login_schema("SocialLoginResponse"),
            400: error(
                "Jeton refusé, rôle + téléphone nécessaires (`registration_required`), ou numéro "
                "à confirmer par code SMS (`phone_verification_required`, avec `social_ticket`)."
            ),
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
            security_log.event("jeton_social_refuse", request, service=provider)
            return Response(
                {"detail": "La connexion a échoué. Réessayez."}, status=status.HTTP_400_BAD_REQUEST
            )

        link = SocialAccount.objects.filter(provider=provider, uid=identity.uid).select_related("user").first()
        user = link.user if link else None
        if user is None and identity.email:
            # Même adresse confirmée par Google/Apple ET chez nous : on relie au compte
            # existant. Une adresse seulement en attente ne suffit pas (prise de contrôle).
            user = User.objects.filter(email=identity.email).first()
        if user is not None:
            if not user.is_active:
                return Response({"detail": SUSPENDED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
            if link is None:
                SocialAccount.objects.get_or_create(user=user, provider=provider, uid=identity.uid)
            if not user.phone_verified:
                return _phone_verification_response(user, request)
            security_log.event("connexion", request, compte=user.pk, methode=provider)
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
        # Nouveau compte : le numéro doit être confirmé par code SMS avant toute connexion.
        # Le lien avec Google / Apple n'est créé qu'à ce moment-là (ticket signé, 15 min) :
        # personne ne peut s'attribuer le numéro d'un autre. Même réponse si le numéro est
        # déjà inscrit (son titulaire reçoit le code et retrouve son compte).
        _require_sms()
        with transaction.atomic():
            target = User.objects.select_for_update().filter(phone=data["phone"]).first()
            if target is None:
                target = User.objects.create_user(phone=data["phone"], role=data["role"])
            elif not target.phone_verified and target.role != data["role"]:
                target.role = data["role"]
                target.save(update_fields=["role"])
        ticket = signing.dumps(
            {"p": provider, "u": identity.uid, "e": identity.email or "", "n": str(target.phone)},
            salt=SOCIAL_TICKET_SALT,
        )
        return _phone_verification_response(target, request, {"social_ticket": ticket})


def _link_social_ticket(user, ticket: str, request) -> None:
    """Après le code SMS : relie le compte Google / Apple mémorisé dans le ticket."""
    try:
        data = signing.loads(ticket, salt=SOCIAL_TICKET_SALT, max_age=SOCIAL_TICKET_MAX_AGE)
    except signing.BadSignature:
        return
    if data.get("n") != str(user.phone):
        return
    if not SocialAccount.objects.filter(provider=data["p"], uid=data["u"]).exists():
        SocialAccount.objects.create(user=user, provider=data["p"], uid=data["u"])
        security_log.event("compte_social_lie", request, compte=user.pk, service=data["p"])
    if data.get("e") and not user.email:
        emails.set_verified_email(user, data["e"])  # confirmée par Google / Apple


class MyPhotoView(APIView):
    """
    GET    /api/accounts/photo/ → ma photo (même en attente de validation)
    POST   /api/accounts/photo/ → envoyer / remplacer ma photo (multipart, champ `photo`)
    DELETE /api/accounts/photo/ → supprimer ma photo
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle("uploads", methods=("POST",))]
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
        user = User.objects.filter(
            photo=f"photos/{name}", photo_status=User.PHOTO_APPROVED, is_active=True
        ).first()
        if user is None:
            raise Http404
        response = FileResponse(user.photo.open("rb"), content_type="image/jpeg")
        # Une heure : une photo retirée ou un compte suspendu disparaît vite des caches
        response["Cache-Control"] = "public, max-age=3600"
        return response


class LogoutView(APIView):
    """
    POST /api/accounts/logout/   { "refresh": "…" }

    Déconnexion de cet appareil : le jeton refresh est mis sur liste noire.
    Répond toujours 200 (un jeton déjà invalide ne change rien).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Comptes"],
        summary="Se déconnecter (cet appareil)",
        auth=[],
        request=inline_serializer(name="LogoutRequest", fields={"refresh": drf_serializers.CharField()}),
        responses={200: MESSAGE_ONLY},
    )
    def post(self, request):
        try:
            RefreshToken(str(_field(request, "refresh") or "")).blacklist()
        except TokenError:
            pass
        return Response({"message": "Déconnecté."})


class LogoutAllView(APIView):
    """POST /api/accounts/logout-all/ — se déconnecter de tous les appareils (y compris celui-ci)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Comptes"],
        summary="Se déconnecter de tous les appareils",
        request=None,
        responses={200: MESSAGE_ONLY, **AUTH_ERRORS},
    )
    def post(self, request):
        request.user.end_all_sessions()
        security_log.event("deconnexion_partout", request, compte=request.user.pk)
        return Response({"message": "Tous vos appareils ont été déconnectés."})


class EmailConfirmView(APIView):
    """POST /api/accounts/email/confirm/   { "token": "…" } — lien reçu par e-mail."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [throttle("auth")]

    @extend_schema(
        tags=["Comptes"],
        summary="Confirmer mon adresse e-mail (lien reçu)",
        auth=[],
        request=EmailConfirmSerializer,
        responses={200: MESSAGE_ONLY, 400: error("Lien invalide ou périmé.")},
    )
    def post(self, request):
        serializer = EmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if emails.confirm(serializer.validated_data["token"]) is None:
            return Response(
                {"detail": "Ce lien n'est plus valable. Demandez-en un nouveau depuis « Sécurité »."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Adresse e-mail confirmée."})


class EmailResendView(APIView):
    """POST /api/accounts/email/resend/ — renvoyer le lien de confirmation."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [throttle("email_send")]

    @extend_schema(
        tags=["Comptes"],
        summary="Renvoyer le lien de confirmation de mon e-mail",
        request=None,
        responses={200: MESSAGE_ONLY, 400: error("Pas d'adresse, ou adresse déjà confirmée."), **AUTH_ERRORS},
    )
    def post(self, request):
        user = request.user
        if not user.pending_email:
            return Response({"detail": "Aucune adresse à confirmer."}, status=status.HTTP_400_BAD_REQUEST)
        emails.send_verification(user)
        return Response({"message": "Lien envoyé. Regardez votre boîte e-mail."})
