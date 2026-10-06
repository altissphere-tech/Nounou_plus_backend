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
