"""
Paramètres de développement local.
Active le mode DEBUG et utilise SQLite (aucune installation requise).
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Base de données locale SQLite (fichier créé automatiquement)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Afficher les emails/OTP dans la console en dev (pas de vrai envoi)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# OTP simulé autorisé (code fixe 123456) — jamais en production
OTP_MOCK_ENABLED = True

# Limites plus larges en développement : on se reconnecte souvent pendant les essais
THROTTLE_RATES = {  # noqa: F405
    **THROTTLE_RATES,  # noqa: F405
    "sms_phone": "30/hour",
    "otp_verify_phone": "60/hour",
    "sms_ip": "100/hour",
    "otp_verify_ip": "100/hour",
    "register": "60/hour",
}
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": THROTTLE_RATES}  # noqa: F405
