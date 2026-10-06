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
