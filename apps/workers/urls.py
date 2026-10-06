"""
Routes de l'app workers.
Montées sous le préfixe /api/workers/ dans config/urls.py.
"""
from django.urls import path
from .views import WorkerProfileCreateView, WorkerProfileListView, WorkerProfileMeView

urlpatterns = [
    # Liste publique des profils vérifiés
    path("", WorkerProfileListView.as_view(), name="workers-list"),
    # Créer son propre profil
    path("profile/", WorkerProfileCreateView.as_view(), name="workers-profile-create"),
    # Voir / modifier son propre profil
    path("profile/me/", WorkerProfileMeView.as_view(), name="workers-profile-me"),
]
