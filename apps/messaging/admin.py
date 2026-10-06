"""
Interface d'administration Django pour la messagerie (modération basique).

L'administrateur peut rechercher des messages et les retirer d'une conversation.
"""
from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "match", "sender", "short_content", "is_hidden", "created_at"]
    list_filter = ["is_hidden", "created_at"]
    search_fields = ["content", "sender__phone"]
    readonly_fields = ["match", "sender", "content", "read_at", "created_at"]
    list_select_related = ["sender", "match__client__user", "match__worker__user"]
    actions = ["hide_messages", "unhide_messages"]

    @admin.display(description="Contenu")
    def short_content(self, obj):
        return obj.content[:80]

    @admin.action(description="Retirer les messages (modération)")
    def hide_messages(self, request, queryset):
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f"{updated} message(s) retiré(s).")

    @admin.action(description="Rétablir les messages")
    def unhide_messages(self, request, queryset):
        updated = queryset.update(is_hidden=False)
        self.message_user(request, f"{updated} message(s) rétabli(s).")

    def has_add_permission(self, request):
        # Les messages sont écrits par les utilisateurs, jamais par l'admin
        return False
