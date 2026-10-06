"""
Paramètres de production — squelette prêt pour PostgreSQL et Redis.
À compléter avant le premier déploiement.
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# PostgreSQL — prêt à l'emploi, aucune réécriture de l'architecture nécessaire
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# Documentation de l'API réservée à l'équipe (comptes admin) en production
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,  # noqa: F405
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
}
