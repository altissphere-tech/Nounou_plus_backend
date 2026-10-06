"""
Routes de l'app services.
Montées sous le préfixe /api/services/ dans config/urls.py.
"""
from django.urls import path

from .views import ServiceListView

urlpatterns = [
    path("", ServiceListView.as_view(), name="services-list"),
]
