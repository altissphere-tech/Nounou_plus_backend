"""
Routes de l'app reports.
Montées sous le préfixe /api/reports/ dans config/urls.py.
"""
from django.urls import path

from .views import ReportView

urlpatterns = [
    path("", ReportView.as_view(), name="reports"),
]
