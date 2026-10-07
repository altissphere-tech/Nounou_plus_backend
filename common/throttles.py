"""
Limites d'essais (anti-abus), en complément des limites par adresse IP de DRF.

Règles validées par le fondateur (valeurs dans config/settings/base.py) :
- codes SMS : 5 envois par heure et par numéro, 20 par heure et par appareil ;
- vérification du code : 10 essais par heure et par numéro ;
- inscription : 10 par heure et par appareil ;
- connexion e-mail / mot de passe oublié : 10 par minute et par appareil,
  20 par heure et par adresse e-mail ;
- messages, signalements, intérêts, envois de fichiers : limites par utilisateur.

L'« appareil » est l'adresse IP. Derrière un proxy (hébergement), régler NUM_PROXIES
dans le .env : sinon l'en-tête X-Forwarded-For, que n'importe qui peut inventer,
n'est jamais pris en compte (voir REST_FRAMEWORK["NUM_PROXIES"]).
"""
import hashlib

import phonenumbers
from rest_framework.throttling import SimpleRateThrottle


class FieldRateThrottle(SimpleRateThrottle):
    """
    Limite par valeur d'un champ envoyé (numéro de téléphone, e-mail), quelle que
    soit l'adresse IP : empêche de viser un même compte depuis plusieurs appareils.
    La valeur est hachée avant d'être utilisée comme clé (pas de donnée personnelle en cache).
    """

    field = ""

    def normalize(self, value: str) -> str:
        return value.strip().lower()

    def get_cache_key(self, request, view):
        value = request.data.get(self.field) if hasattr(request, "data") else None
        if not value:
            return None
        ident = hashlib.sha256(self.normalize(str(value)).encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class PhoneThrottle(FieldRateThrottle):
    field = "phone"

    def normalize(self, value: str) -> str:
        # « 0812345678 » et « +243812345678 » désignent le même numéro
        try:
            number = phonenumbers.parse(value, "CD")
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            return value.strip()


class SmsPhoneThrottle(PhoneThrottle):
    scope = "sms_phone"


class OtpVerifyPhoneThrottle(PhoneThrottle):
    scope = "otp_verify_phone"


class LoginEmailThrottle(FieldRateThrottle):
    scope = "login_email"
    field = "email"


class ScopeThrottle(SimpleRateThrottle):
    """
    Limite par utilisateur connecté, sinon par adresse IP. Seules les méthodes
    listées dans `methods` sont comptées (ex : envoyer un message, pas les lire).
    """

    methods = ("POST", "PUT", "PATCH", "DELETE")

    def allow_request(self, request, view):
        if request.method not in self.methods:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        ident = f"user-{user.pk}" if user is not None and user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


def throttle(scope: str, methods=("POST", "PUT", "PATCH", "DELETE")) -> type[ScopeThrottle]:
    """Crée une limite pour la portée `scope` (taux défini dans DEFAULT_THROTTLE_RATES)."""
    name = "".join(part.title() for part in scope.split("_")) + "Throttle"
    return type(name, (ScopeThrottle,), {"scope": scope, "methods": methods})
