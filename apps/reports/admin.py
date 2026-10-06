"""
Interface d'administration Django pour traiter les signalements.

Décisions possibles : classer sans suite, avertir (message affiché à la personne
signalée), suspendre le compte (plus de connexion, disparition des listes).
"""
from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["target", "category", "status", "reports_against_target", "created_at", "decided_at"]
    list_filter = ["status", "category"]
    search_fields = ["target__phone", "reporter__phone", "description"]
    list_select_related = ["target", "reporter"]
    fields = [
        "target",
        "reporter",
        "category",
        "description",
        "created_at",
        "status",
        "user_message",
        "admin_note",
        "decided_by",
        "decided_at",
    ]
    readonly_fields = [
        "target",
        "reporter",
        "category",
        "description",
        "created_at",
        "decided_by",
        "decided_at",
    ]
    actions = ["dismiss_reports"]

    def has_add_permission(self, request):
        # Les signalements sont envoyés par les utilisateurs via l'API
        return False

    @admin.display(description="Signalements reçus par cette personne")
    def reports_against_target(self, obj):
        return obj.target.reports_received.count()

    def save_model(self, request, obj, form, change):
        if change and {"status", "user_message"} & set(form.changed_data):
            previous_status = form.initial.get("status")
            obj.decide(request.user, obj.status, obj.user_message, previous_status=previous_status)
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Classer sans suite")
    def dismiss_reports(self, request, queryset):
        for report in queryset.select_related("target"):
            report.decide(request.user, Report.STATUS_DISMISSED)
        self.message_user(request, f"{queryset.count()} signalement(s) classé(s) sans suite.")
