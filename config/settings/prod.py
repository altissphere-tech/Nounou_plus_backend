"""
Paramètres de production — squelette prêt pour PostgreSQL.
À compléter avant le premier déploiement (voir docs/SECURITE.md, « Avant la mise en ligne »).
"""
from .base import *  # noqa: F401, F403
from decouple import config
from django.core.exceptions import ImproperlyConfigured

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

# Connexion chiffrée obligatoire vers PostgreSQL quand la base est sur une autre machine
_db_is_local = DATABASES["default"]["HOST"] in ("localhost", "127.0.0.1", "::1", "")
DATABASES["default"]["OPTIONS"] = {
    "sslmode": config("DB_SSLMODE", default="prefer" if _db_is_local else "require")
}

# L'adresse de l'administration doit être changée (moins exposée aux robots)
if ADMIN_URL.strip("/") == "admin":  # noqa: F405
    raise ImproperlyConfigured("Choisissez une ADMIN_URL non évidente pour la production (ex : gestion-xxxx/).")

# Les liens envoyés par e-mail (mot de passe oublié, confirmation) pointent vers
# l'application : adresse obligatoire et en HTTPS
if not FRONTEND_URL.startswith("https://"):  # noqa: F405
    raise ImproperlyConfigured("FRONTEND_URL doit être l'adresse HTTPS de l'application (ex : https://nounou-plus.com).")

# Fichiers envoyés (photos, pièces d'identité) lisibles par le seul compte du serveur
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700

# Cache partagé (base de données) : les limites d'essais sont communes à tous les
# processus du serveur. Créer la table une fois : python manage.py createcachetable
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "nounou_cache"}
}

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
# À activer quand TOUS les sous-domaines sont en HTTPS (sinon ils deviennent inaccessibles)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
SECURE_HSTS_PRELOAD = config("HSTS_PRELOAD", default=False, cast=bool)
# Derrière un proxy (nginx, hébergeur) qui reçoit le HTTPS : sans ce réglage, Django
# croit que la connexion n'est pas chiffrée et redirige en boucle.
if REST_FRAMEWORK["NUM_PROXIES"]:  # noqa: F405
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS", default="", cast=lambda v: [s.strip() for s in v.split(",") if s.strip()]
)

# E-mails réels (mot de passe oublié, confirmation d'adresse)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# Documentation de l'API réservée à l'équipe (comptes admin) en production
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,  # noqa: F405
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
}

# Erreurs du serveur (500) écrites dans le journal : sans cela, elles seraient perdues
# (aucune adresse ADMINS pour les recevoir par e-mail)
LOGGING = {
    **LOGGING,  # noqa: F405
    "handlers": {
        **LOGGING["handlers"],  # noqa: F405
        "errors_console": {"class": "logging.StreamHandler", "level": "ERROR"},
    },
    "loggers": {
        **LOGGING["loggers"],  # noqa: F405
        "django": {"handlers": ["errors_console"], "level": "ERROR", "propagate": False},
    },
}
