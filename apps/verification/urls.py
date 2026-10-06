"""
Routes de l'app verification.
Montées sous le préfixe /api/verification/ dans config/urls.py.
"""
from django.urls import path

from .views import ReferenceDetailView, ReferenceListView, VerificationDocumentsView

urlpatterns = [
    path("documents/", VerificationDocumentsView.as_view(), name="verification-documents"),
    path("references/", ReferenceListView.as_view(), name="verification-references"),
    path("references/<int:pk>/", ReferenceDetailView.as_view(), name="verification-reference-detail"),
]
