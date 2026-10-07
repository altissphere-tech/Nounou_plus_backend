"""
Routes de l'app accounts.
Ces URLs sont montées sous le préfixe /api/accounts/ dans config/urls.py.
"""
from django.urls import path
from .views import (
    AuthOptionsView,
    EmailChangeView,
    EmailConfirmView,
    EmailLoginView,
    EmailResendView,
    LogoutAllView,
    LogoutView,
    MeView,
    MyPhotoView,
    OTPRequestView,
    OTPVerifyView,
    PasswordChangeView,
    PasswordForgotView,
    PasswordResetView,
    RegisterView,
    SocialLoginView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("otp/request/", OTPRequestView.as_view(), name="accounts-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="accounts-otp-verify"),
    path("me/", MeView.as_view(), name="accounts-me"),
    path("auth-options/", AuthOptionsView.as_view(), name="accounts-auth-options"),
    path("login/", EmailLoginView.as_view(), name="accounts-login"),
    path("social/", SocialLoginView.as_view(), name="accounts-social"),
    path("password/forgot/", PasswordForgotView.as_view(), name="accounts-password-forgot"),
    path("password/reset/", PasswordResetView.as_view(), name="accounts-password-reset"),
    path("password/change/", PasswordChangeView.as_view(), name="accounts-password-change"),
    path("email/", EmailChangeView.as_view(), name="accounts-email"),
    path("email/confirm/", EmailConfirmView.as_view(), name="accounts-email-confirm"),
    path("email/resend/", EmailResendView.as_view(), name="accounts-email-resend"),
    path("photo/", MyPhotoView.as_view(), name="accounts-photo"),
    path("logout/", LogoutView.as_view(), name="accounts-logout"),
    path("logout-all/", LogoutAllView.as_view(), name="accounts-logout-all"),
]
