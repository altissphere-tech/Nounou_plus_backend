"""
Vérification des connexions Google et Apple.

L'application (sur le téléphone) obtient de Google ou d'Apple un « jeton d'identité »
signé. Le serveur vérifie ici la signature avec les clés publiques du service, puis
lit l'identifiant et l'e-mail de la personne. Aucun mot de passe Google/Apple ne
transite par NOUNOU+.

Configuration (fichier .env) :
- GOOGLE_CLIENT_ID : identifiant de l'application créé sur console.cloud.google.com
- APPLE_CLIENT_ID  : « Services ID » créé sur developer.apple.com
Tant qu'une valeur est vide, le bouton correspondant est désactivé.
"""
from dataclasses import dataclass

import jwt
from django.conf import settings

PROVIDERS = {
    "google": {
        "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
        "issuers": ["https://accounts.google.com", "accounts.google.com"],
        "setting": "GOOGLE_CLIENT_ID",
    },
    "apple": {
        "jwks_url": "https://appleid.apple.com/auth/keys",
        "issuers": ["https://appleid.apple.com"],
        "setting": "APPLE_CLIENT_ID",
    },
}

_jwks_clients: dict[str, jwt.PyJWKClient] = {}


class SocialAuthError(Exception):
    """Jeton refusé (signature, émetteur, destinataire ou date d'expiration incorrects)."""


@dataclass
class SocialIdentity:
    uid: str
    email: str | None  # seulement si le service confirme que l'adresse est vérifiée


def client_id(provider: str) -> str:
    return getattr(settings, PROVIDERS[provider]["setting"], "") or ""


def verify_id_token(provider: str, token: str) -> SocialIdentity:
    """Vérifie le jeton et renvoie l'identité. Lève SocialAuthError s'il est invalide."""
    config = PROVIDERS[provider]
    audience = client_id(provider)
    if provider not in _jwks_clients:
        _jwks_clients[provider] = jwt.PyJWKClient(config["jwks_url"], cache_keys=True)
    try:
        key = _jwks_clients[provider].get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=config["issuers"],
        )
    except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
        raise SocialAuthError(str(exc)) from exc
    verified = claims.get("email_verified") in (True, "true")
    return SocialIdentity(uid=str(claims["sub"]), email=claims.get("email") if verified else None)
