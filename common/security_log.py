"""
Journal de sécurité « nounou.security ».

Règle : jamais de mot de passe, code, jeton ni numéro / e-mail complet.
On note un identifiant de compte, ou l'empreinte courte d'un identifiant tapé
(permet de repérer « 200 essais sur le même e-mail » sans écrire l'e-mail).
"""
import hashlib
import logging

from rest_framework.exceptions import Throttled
from rest_framework.throttling import BaseThrottle
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("nounou.security")


def fingerprint(value) -> str:
    """Empreinte courte et non réversible d'un identifiant (e-mail, numéro)."""
    return hashlib.sha256(str(value).strip().lower().encode()).hexdigest()[:12] if value else "-"


def client_ip(request) -> str:
    # Même lecture de l'adresse que les limites d'essais (tient compte de NUM_PROXIES)
    return BaseThrottle().get_ident(request)


def event(name: str, request=None, **fields) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    ip = client_ip(request) if request is not None else "-"
    logger.info("%s ip=%s %s", name, ip, details)


def exception_handler(exc, context):
    """Gestion d'erreurs habituelle de DRF, plus une ligne au journal quand une limite est atteinte."""
    if isinstance(exc, Throttled):
        request = context.get("request")
        view = context.get("view")
        event("limite_atteinte", request, vue=type(view).__name__ if view else "-", chemin=getattr(request, "path", "-"))
    return drf_exception_handler(exc, context)
