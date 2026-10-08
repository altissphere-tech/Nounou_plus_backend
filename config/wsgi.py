"""
Point d'entrée WSGI pour les déploiements sur serveur (gunicorn, etc.).

Le réglage DJANGO_SETTINGS_MODULE est obligatoire ici (variable d'environnement du
service, ou ligne du fichier .env) : sans lui, le serveur refuse de démarrer au lieu
de tourner par erreur en mode développement (code SMS 123456 actif).
"""
import os

from decouple import config
from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

settings_module = os.environ.get("DJANGO_SETTINGS_MODULE") or config("DJANGO_SETTINGS_MODULE", default="")
if not settings_module:
    raise ImproperlyConfigured(
        "DJANGO_SETTINGS_MODULE manquant : indiquez config.settings.prod sur le serveur."
    )
os.environ["DJANGO_SETTINGS_MODULE"] = settings_module

application = get_wsgi_application()
