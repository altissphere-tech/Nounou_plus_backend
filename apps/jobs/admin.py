"""
Interface d'administration Django pour les annonces.
"""
from django.contrib import admin

from .models import JobRequest


@admin.register(JobRequest)
class JobRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "client", "service", "availability", "budget", "location", "status", "created_at"]
    list_filter = ["status", "service", "availability"]
    search_fields = ["title", "description", "location", "client__first_name", "client__user__phone"]
    list_select_related = ["client__user", "service"]
    readonly_fields = ["created_at", "updated_at"]
