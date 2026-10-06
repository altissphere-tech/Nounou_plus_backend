"""
Routes de l'app accounts.
Ces URLs sont montées sous le préfixe /api/accounts/ dans config/urls.py.
"""
from django.urls import path
from .views import MeView, OTPRequestView, OTPVerifyView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("otp/request/", OTPRequestView.as_view(), name="accounts-otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="accounts-otp-verify"),
    path("me/", MeView.as_view(), name="accounts-me"),
]
