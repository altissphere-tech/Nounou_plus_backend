"""
Interface d'administration Django pour les profils clients.
"""
from django.contrib import admin

from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "user",
        "location",
        "availability_needed",
        "budget",
        "created_at",
    ]
    list_filter = ["availability_needed", "services_needed"]
    search_fields = ["first_name", "last_name", "user__phone", "location"]
    filter_horizontal = ["services_needed"]
    readonly_fields = ["created_at", "updated_at"]
