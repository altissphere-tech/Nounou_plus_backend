"""
Jetons de connexion (JWT) révocables.

Un JWT reste normalement valable jusqu'à sa date d'expiration, même après une
déconnexion ou un changement de mot de passe. Pour pouvoir « chasser » un voleur
de session, deux mécanismes s'ajoutent :

1. Déconnexion d'un appareil : son jeton « refresh » est mis sur liste noire
   (application token_blacklist de simplejwt) ; il ne peut plus servir.
2. Déconnexion partout (changement ou réinitialisation du mot de passe,
   « Se déconnecter de tous les appareils ») : `User.token_version` augmente ;
   chaque jeton porte la version en cours à sa création (« ver ») et tout jeton
   d'une ancienne version est refusé, access comme refresh.
"""
import time

from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as BaseTokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

REVOKED_MESSAGE = "Votre session a expiré. Reconnectez-vous."


VERSION_CLAIM = "ver"
# Moment de la connexion (code SMS, mot de passe, Google / Apple). Il reste le même
# quand les jetons sont renouvelés : il dit depuis combien de temps la personne a
# prouvé son identité.
AUTH_TIME_CLAIM = "auth_time"
RECENT_LOGIN_SECONDS = 10 * 60


def tokens_for(user) -> RefreshToken:
    """Crée les jetons d'un utilisateur, marqués avec sa version de session actuelle."""
    refresh = RefreshToken.for_user(user)
    refresh[VERSION_CLAIM] = user.token_version  # recopié dans le jeton access
    refresh[AUTH_TIME_CLAIM] = int(time.time())
    return refresh


def recent_login(request) -> bool:
    """True si la personne s'est connectée il y a moins de 10 minutes (pas un simple renouvellement)."""
    token = getattr(request, "auth", None)
    if token is None:
        return False
    try:
        auth_time = int(token.get(AUTH_TIME_CLAIM, 0))
    except (TypeError, ValueError):
        return False
    return 0 <= time.time() - auth_time <= RECENT_LOGIN_SECONDS


def token_revoked(user, token) -> bool:
    """True si le jeton date d'avant la dernière « déconnexion partout » de l'utilisateur."""
    return int(token.get(VERSION_CLAIM, 0)) != user.token_version


class JWTAuthentication(BaseJWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if token_revoked(user, validated_token):
            raise AuthenticationFailed(REVOKED_MESSAGE, code="token_revoked")
        return user


class TokenRefreshSerializer(BaseTokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])  # signature, expiration et liste noire
        user = get_user_model().objects.filter(
            **{api_settings.USER_ID_FIELD: refresh.payload.get(api_settings.USER_ID_CLAIM)}
        ).first()
        if user is None or not user.is_active or token_revoked(user, refresh):
            raise AuthenticationFailed(REVOKED_MESSAGE, code="token_revoked")
        return super().validate(attrs)
