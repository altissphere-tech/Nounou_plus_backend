"""
Point d'entrée WSGI pour les déploiements sur serveur (gunicorn, etc.).
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
