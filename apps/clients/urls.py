"""
Routes de l'app clients.
Montées sous le préfixe /api/clients/ dans config/urls.py.
"""
from django.urls import path

from .views import ClientProfileCreateView, ClientProfileListView, ClientProfileMeView

urlpatterns = [
    # Liste des besoins clients (visible par les travailleurs)
    path("", ClientProfileListView.as_view(), name="clients-list"),
    # Créer son propre profil
    path("profile/", ClientProfileCreateView.as_view(), name="clients-profile-create"),
    # Voir / modifier son propre profil
    path("profile/me/", ClientProfileMeView.as_view(), name="clients-profile-me"),
]
