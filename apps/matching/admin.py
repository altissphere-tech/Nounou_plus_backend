"""
Interface d'administration Django pour les mises en relation.
L'administrateur voit le statut réel (y compris les refus).
"""
from django.contrib import admin

from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["client", "worker", "client_decision", "worker_decision", "status", "mutual_at", "created_at"]
    list_filter = ["client_decision", "worker_decision"]
    search_fields = [
        "client__first_name",
        "client__last_name",
        "client__user__phone",
        "worker__first_name",
        "worker__last_name",
        "worker__user__phone",
    ]
    readonly_fields = ["mutual_at", "created_at", "updated_at"]
    list_select_related = ["client__user", "worker__user"]

    @admin.display(description="Statut")
    def status(self, obj):
        return obj.status
