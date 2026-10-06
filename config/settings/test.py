"""
Paramètres de test — utilise une base de données en mémoire pour la rapidité.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Base de données en mémoire : les tests sont plus rapides et ne laissent aucun fichier
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Désactiver le hachage de mot de passe pour accélérer les tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# OTP simulé autorisé (code fixe 123456) — jamais en production
OTP_MOCK_ENABLED = True

# Pas de limite d'essais pendant les tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"auth": "10000/min"},
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
