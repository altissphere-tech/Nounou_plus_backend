"""
Interface d'administration Django pour les comptes NOUNOU+.
Accessible sur /admin/ avec un compte créé via `python manage.py createsuperuser`.
"""
from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["phone", "role", "phone_verified", "is_active", "is_staff", "created_at"]
    list_filter = ["role", "phone_verified", "is_active", "is_staff"]
    search_fields = ["phone"]
    ordering = ["-created_at"]
    # Le code OTP et le mot de passe ne sont jamais affichés ni modifiables ici
    exclude = ["password", "otp_code"]
    readonly_fields = ["created_at", "last_login"]
