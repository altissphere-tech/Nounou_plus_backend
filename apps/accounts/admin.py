"""
Interface d'administration Django pour les comptes NOUNOU+.
Accessible sur /admin/ avec un compte créé via `python manage.py createsuperuser`.
"""
from django.contrib import admin, messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from . import photos
from .models import PhotoToReview, SocialAccount, User


class SocialAccountInline(admin.TabularInline):
    model = SocialAccount
    extra = 0
    can_delete = True
    readonly_fields = ["provider", "uid", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["phone", "email", "role", "phone_verified", "is_active", "is_staff", "created_at"]
    list_filter = ["role", "phone_verified", "photo_status", "is_active", "is_staff"]
    search_fields = ["phone", "email"]
    inlines = [SocialAccountInline]
    ordering = ["-created_at"]
    # Le code OTP et le mot de passe ne sont jamais affichés ni modifiables ici
    # La photo se gère dans « Photos de profil »
    exclude = ["password", "otp_code", "photo", "photo_status", "photo_rejection_reason"]
    readonly_fields = ["created_at", "last_login"]


@admin.register(PhotoToReview)
class PhotoToReviewAdmin(admin.ModelAdmin):
    """
    Photos de profil à valider. Une photo n'est montrée aux autres qu'après validation.
    Refuser une photo la supprime ; la personne est notifiée avec le motif.
    """

    list_display = ["thumbnail", "phone", "role", "photo_status", "photo_rejection_reason"]
    list_filter = ["photo_status", "role"]
    search_fields = ["phone", "email"]
    fields = ["thumbnail_large", "phone", "role", "photo_status", "photo_rejection_reason"]
    readonly_fields = ["thumbnail_large", "phone", "role", "photo_status"]
    actions = ["approve_photos", "reject_photos"]

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(photo_status=User.PHOTO_NONE)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # supprimer ici effacerait le compte entier

    def get_urls(self):
        custom = [
            path(
                "<int:pk>/image/",
                self.admin_site.admin_view(self.image),
                name="accounts_phototoreview_image",
            )
        ]
        return custom + super().get_urls()

    def image(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if not self.has_view_permission(request) or not user.photo:
            raise Http404
        return FileResponse(user.photo.open("rb"), content_type="image/jpeg")

    def _img(self, obj, size):
        if not obj.photo:
            return "—"
        url = reverse("admin:accounts_phototoreview_image", args=[obj.pk])
        return format_html(
            '<img src="{}" style="width:{}px;height:{}px;object-fit:cover;border-radius:50%">',
            url,
            size,
            size,
        )

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        return self._img(obj, 56)

    @admin.display(description="Photo")
    def thumbnail_large(self, obj):
        return self._img(obj, 240)

    @admin.action(description="Valider les photos sélectionnées")
    def approve_photos(self, request, queryset):
        count = 0
        for user in queryset.filter(photo_status=User.PHOTO_PENDING):
            photos.review_photo(user, approved=True)
            count += 1
        self.message_user(request, f"{count} photo(s) validée(s).", level=messages.SUCCESS)

    @admin.action(description="Refuser les photos sélectionnées (motif : champ « Motif du refus »)")
    def reject_photos(self, request, queryset):
        count = 0
        for user in queryset.filter(photo_status__in=[User.PHOTO_PENDING, User.PHOTO_APPROVED]):
            photos.review_photo(user, approved=False, reason=user.photo_rejection_reason)
            count += 1
        self.message_user(request, f"{count} photo(s) refusée(s).")
