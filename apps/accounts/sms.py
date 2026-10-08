"""
Envoi des codes SMS.

En développement (OTP_MOCK_ENABLED) : aucun SMS, le code s'affiche dans la console
du serveur. En production : à brancher sur le fournisseur choisi (voir
docs/DEPLOIEMENT.md) ; tant qu'aucun n'est configuré, l'envoi est indisponible
(réponse 503) au lieu d'accepter un code connu de tous.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def available() -> bool:
    return bool(settings.OTP_MOCK_ENABLED)


def send_code(phone: str, code: str) -> None:
    if settings.OTP_MOCK_ENABLED:
        logger.warning("[SMS SIMULÉ] %s → code : %s (développement uniquement)", phone, code)
        return
    raise RuntimeError("Aucun fournisseur SMS configuré.")
