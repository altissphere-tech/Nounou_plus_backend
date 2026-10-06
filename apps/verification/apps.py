"""
Configuration de l'app verification pour Django.
"""
from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.verification"
    verbose_name = "Vérification des documents"
