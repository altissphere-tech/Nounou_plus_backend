from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Consultation seule (utile pour aider une personne qui dit n'avoir rien reçu)."""

    list_display = ["user", "kind", "count", "created_at", "read_at"]
    list_filter = ["kind"]
    search_fields = ["user__phone", "user__email"]
    readonly_fields = ["user", "kind", "params", "count", "read_at", "created_at"]

    def has_add_permission(self, request):
        return False
