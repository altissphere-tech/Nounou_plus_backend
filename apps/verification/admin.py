"""
Interface d'administration Django pour la vérification des documents.

L'administrateur :
- ouvre le document via un lien protégé (réservé aux comptes admin) ;
- le valide ou le rejette (avec un motif visible par le travailleur).
Valider une pièce d'identité accorde le badge « vérifié » au travailleur.
"""
from django.contrib import admin, messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from .models import VerificationRecord, WorkerReference


@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ["worker", "doc_type", "status", "document_link", "created_at", "reviewed_at"]
    list_filter = ["status", "doc_type"]
    search_fields = ["worker__first_name", "worker__last_name", "worker__user__phone"]
    list_select_related = ["worker__user"]
    fields = [
        "worker",
        "doc_type",
        "document_link",
        "status",
        "rejection_reason",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ]
    readonly_fields = ["worker", "doc_type", "document_link", "reviewed_by", "reviewed_at", "created_at"]
    actions = ["approve_documents"]

    def has_add_permission(self, request):
        # Les documents sont envoyés par les travailleurs via l'API
        return False

    # --- Accès protégé au fichier -------------------------------------

    def get_urls(self):
        custom = [
            path(
                "<int:pk>/fichier/",
                self.admin_site.admin_view(self.download_document),
                name="verification_verificationrecord_file",
            ),
        ]
        return custom + super().get_urls()

    def download_document(self, request, pk):
        """Ouvre le fichier — uniquement pour un administrateur connecté."""
        if not self.has_view_permission(request):
            raise Http404
        record = get_object_or_404(VerificationRecord, pk=pk)
        if not record.file:
            raise Http404
        return FileResponse(record.file.open("rb"))

    @admin.display(description="Document")
    def document_link(self, obj):
        if not obj.pk or not obj.file:
            return "—"
        url = reverse("admin:verification_verificationrecord_file", args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Ouvrir le document</a>', url)

    # --- Décision de l'administrateur -----------------------------------

    def save_model(self, request, obj, form, change):
        if change and {"status", "rejection_reason"} & set(form.changed_data):
            if obj.status == VerificationRecord.STATUS_REJECTED and not obj.rejection_reason.strip():
                obj.rejection_reason = "Document illisible ou non conforme."
            obj.review(request.user, obj.status, obj.rejection_reason)
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Valider les documents sélectionnés")
    def approve_documents(self, request, queryset):
        for record in queryset.select_related("worker"):
            record.review(request.user, VerificationRecord.STATUS_APPROVED)
        self.message_user(
            request, f"{queryset.count()} document(s) validé(s).", level=messages.SUCCESS
        )


@admin.register(WorkerReference)
class WorkerReferenceAdmin(admin.ModelAdmin):
    """
    Références à appeler. Après l'appel, choisir « Vérifiée » ou « Non confirmée »
    (le travailleur est notifié ; la note reste interne à l'équipe).
    """

    list_display = ["name", "phone", "relationship", "worker", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "phone", "worker__first_name", "worker__last_name"]
    list_select_related = ["worker__user"]
    fields = [
        "worker",
        "name",
        "phone",
        "relationship",
        "status",
        "team_note",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ]
    readonly_fields = ["worker", "name", "phone", "relationship", "reviewed_by", "reviewed_at", "created_at"]
    actions = ["mark_verified", "mark_not_confirmed"]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.review(request.user, obj.status)
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Marquer comme vérifiées (appel concluant)")
    def mark_verified(self, request, queryset):
        for reference in queryset.select_related("worker__user"):
            reference.review(request.user, WorkerReference.STATUS_VERIFIED)
        self.message_user(
            request, f"{queryset.count()} référence(s) vérifiée(s).", level=messages.SUCCESS
        )

    @admin.action(description="Marquer comme non confirmées")
    def mark_not_confirmed(self, request, queryset):
        for reference in queryset.select_related("worker__user"):
            reference.review(request.user, WorkerReference.STATUS_REJECTED)
        self.message_user(request, f"{queryset.count()} référence(s) non confirmée(s).")
