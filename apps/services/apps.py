"""
Configuration de l'app services pour Django.
"""
from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
    verbose_name = "Services"
