"""
Interface d'administration Django pour le catalogue de services.
"""
from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["slug", "label"]
    search_fields = ["slug", "label"]
