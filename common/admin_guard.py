"""
Limite d'essais sur la page de connexion de l'administration.

Après 10 échecs en 15 minutes depuis un même appareil, ou pour un même identifiant,
la page refuse les nouveaux essais pendant 15 minutes : deviner un mot de passe de
l'équipe devient impraticable.
"""
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse

from common.security_log import client_ip, event, fingerprint

MAX_FAILURES = 10
WINDOW_SECONDS = 15 * 60
BLOCKED_MESSAGE = "Trop d'essais de connexion. Réessayez dans 15 minutes."


def _keys(request) -> list[str]:
    return [
        f"admin-login:ip:{client_ip(request)}",
        f"admin-login:user:{fingerprint(request.POST.get('username'))}",
    ]


def limit_login_attempts(login_view):
    @wraps(login_view)
    def wrapper(request, *args, **kwargs):
        if request.method != "POST":
            return login_view(request, *args, **kwargs)
        keys = _keys(request)
        if any(cache.get(key, 0) >= MAX_FAILURES for key in keys):
            event("admin_connexion_bloquee", request, identifiant=fingerprint(request.POST.get("username")))
            return HttpResponse(BLOCKED_MESSAGE, status=429, content_type="text/plain; charset=utf-8")
        response = login_view(request, *args, **kwargs)
        if not request.user.is_authenticated:  # échec : le formulaire est réaffiché
            for key in keys:
                cache.add(key, 0, WINDOW_SECONDS)
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, WINDOW_SECONDS)
            event("admin_connexion_refusee", request, identifiant=fingerprint(request.POST.get("username")))
        return response

    return wrapper
