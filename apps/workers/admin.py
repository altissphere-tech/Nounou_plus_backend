"""
Interface d'administration Django pour les profils travailleurs.

C'est ici que l'administrateur valide manuellement un profil (badge « vérifié »).
Rappel : ce badge ne constitue pas une garantie d'absence de risque.
"""
from django.contrib import admin

from .models import WorkerProfile


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "user",
        "availability",
        "location",
        "is_verified",
        "created_at",
    ]
    list_filter = ["is_verified", "availability", "services"]
    search_fields = ["first_name", "last_name", "user__phone", "location"]
    filter_horizontal = ["services"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["mark_verified", "mark_unverified"]

    @admin.action(description="Marquer comme vérifié")
    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} profil(s) marqué(s) comme vérifié(s).")

    @admin.action(description="Retirer le badge vérifié")
    def mark_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} profil(s) n'est/ne sont plus vérifié(s).")
