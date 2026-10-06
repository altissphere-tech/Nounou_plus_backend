"""
Paramètres Django communs à tous les environnements (dev, prod, test).
Aucune valeur sensible ici — tout est lu depuis les variables d'environnement via decouple.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config

# Racine du projet (dossier nounou-backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Clé secrète (jamais dans le code, toujours dans .env) ---
SECRET_KEY = config("SECRET_KEY")

# --- Applications installées ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Bibliothèques tierces
    "rest_framework",
    "rest_framework_simplejwt",
    "phonenumber_field",
    "drf_spectacular",
    "drf_spectacular_sidecar",  # fichiers de la page de documentation, servis localement
    # Apps NOUNOU+
    "apps.accounts",
    "apps.services",
    "apps.workers",
    "apps.clients",
    "apps.jobs",
    "apps.matching",
    "apps.messaging",
    "apps.verification",
    "apps.reviews",
    "apps.reports",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Modèle utilisateur personnalisé ---
AUTH_USER_MODEL = "accounts.User"

# --- Internationalisation ---
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lubumbashi"
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques ---
STATIC_URL = "/static/"

# --- Fichiers envoyés par les utilisateurs (documents de vérification) ---
# Stockés sur le disque local en développement (dossier media/, ignoré par git).
# Volontairement AUCUNE adresse publique ne sert ces fichiers : l'admin les ouvre
# via une page protégée. Pour passer à un stockage S3 plus tard, il suffira de
# changer le réglage STORAGES, sans toucher au code des apps.
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    # Génère la description de l'API (OpenAPI) utilisée par la documentation interactive
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --- Documentation interactive de l'API (/api/docs/) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "API NOUNOU+",
    "DESCRIPTION": (
        "Marketplace de mise en relation entre familles et travailleurs domestiques "
        "à Lubumbashi.\n\n"
        "**Se connecter dans cette page :**\n"
        "1. `POST /api/accounts/register/` pour un nouveau compte, ou "
        "`POST /api/accounts/otp/request/` pour un compte existant (un code ne sert qu'une fois) ;\n"
        "2. `POST /api/accounts/otp/verify/` avec le code `123456` (OTP simulé en "
        "développement) → copiez la valeur `access` ;\n"
        "3. cliquez sur **Authorize** en haut de la page et collez-la.\n\n"
        "Le téléphone et le nom complet de l'autre partie ne sont visibles qu'après "
        "un match mutuel. Le badge « vérifié » ne constitue pas une garantie "
        "d'absence de risque."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Fichiers de la page servis par le projet (pas de dépendance à un site externe)
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,  # garde le token après un rechargement de la page
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
    # Noms clairs pour les listes de valeurs partagées par plusieurs endpoints
    "ENUM_NAME_OVERRIDES": {
        "AvailabilityEnum": "common.choices.AVAILABILITY_CHOICES",
        "UserRoleEnum": "apps.accounts.models.User.ROLE_CHOICES",
        "RegisterRoleEnum": ["client", "travailleur"],
        "JobStatusEnum": "apps.jobs.models.JobRequest.STATUS_CHOICES",
        "VerificationStatusEnum": "apps.verification.models.VerificationRecord.STATUS_CHOICES",
    },
    "TAGS": [
        {"name": "Comptes", "description": "Inscription, connexion par code SMS, profil du compte."},
        {"name": "Services", "description": "Catalogue des services (nounou, ménage, cuisine)."},
        {"name": "Travailleurs", "description": "Profils des travailleurs et recherche."},
        {"name": "Clients", "description": "Profils des familles et recherche des besoins."},
        {"name": "Annonces", "description": "Annonces publiées par les familles."},
        {"name": "Mise en relation", "description": "Intérêt, match mutuel, refus."},
        {"name": "Messagerie", "description": "Conversation après un match mutuel."},
        {"name": "Vérification", "description": "Documents des travailleurs et badge « vérifié »."},
        {"name": "Évaluations", "description": "Notes après la période d'essai."},
        {"name": "Signalements", "description": "Signaler un profil (anonyme)."},
    ],
}

# --- JWT (tokens d'authentification) ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- OTP simulé (code fixe 123456, sans envoi de SMS) ---
# Désactivé par défaut : seuls dev.py et test.py l'activent.
# Tant qu'un vrai fournisseur SMS n'est pas branché (V2), la connexion
# est donc impossible en production — c'est voulu, pour ne jamais
# accepter le code 123456 sur un serveur réel.
OTP_MOCK_ENABLED = False

# --- Évaluations ---
# Nombre de jours après le premier match mutuel avant de pouvoir s'évaluer
# (laisse le temps d'une période d'essai).
REVIEW_DELAY_DAYS = 7

# --- Format des numéros de téléphone (RDC = CD) ---
PHONENUMBER_DEFAULT_REGION = "CD"
