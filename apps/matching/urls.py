"""
Routes de l'app matching.
Montées sous le préfixe /api/matches/ dans config/urls.py.
"""
from django.urls import path

from .views import MatchDeclineView, MatchInterestView, MatchListView

urlpatterns = [
    # Mes mises en relation
    path("", MatchListView.as_view(), name="matches-list"),
    # Manifester son intérêt (ou accepter un intérêt reçu)
    path("interest/", MatchInterestView.as_view(), name="matches-interest"),
    # Refuser une mise en relation
    path("<int:pk>/decline/", MatchDeclineView.as_view(), name="matches-decline"),
]
