"""
Interface d'administration Django pour les évaluations (vue globale + modération).
"""
from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["author", "target", "overall", "short_comment", "comment_hidden", "created_at"]
    list_filter = ["comment_hidden", "created_at"]
    search_fields = ["author__phone", "target__phone", "comment"]
    list_select_related = ["author", "target"]
    readonly_fields = [
        "match",
        "author",
        "target",
        "punctuality",
        "competence",
        "reliability",
        "respect",
        "clarity",
        "payment_on_time",
        "overall",
        "comment",
        "created_at",
    ]
    actions = ["hide_comments", "unhide_comments"]

    def has_add_permission(self, request):
        # Les évaluations sont laissées par les utilisateurs, jamais par l'admin
        return False

    @admin.display(description="Commentaire")
    def short_comment(self, obj):
        return obj.comment[:80]

    @admin.action(description="Retirer les commentaires (modération)")
    def hide_comments(self, request, queryset):
        updated = queryset.update(comment_hidden=True)
        self.message_user(request, f"{updated} commentaire(s) retiré(s).")

    @admin.action(description="Rétablir les commentaires")
    def unhide_comments(self, request, queryset):
        updated = queryset.update(comment_hidden=False)
        self.message_user(request, f"{updated} commentaire(s) rétabli(s).")
