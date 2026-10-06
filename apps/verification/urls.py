"""
Routes de l'app verification.
Montées sous le préfixe /api/verification/ dans config/urls.py.
"""
from django.urls import path

from .views import VerificationDocumentsView

urlpatterns = [
    path("documents/", VerificationDocumentsView.as_view(), name="verification-documents"),
]
