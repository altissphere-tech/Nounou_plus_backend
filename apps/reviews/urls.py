"""
Routes de l'app reviews.
Montées sous le préfixe /api/reviews/ dans config/urls.py.
(L'envoi d'une évaluation se fait sur /api/matches/<id>/review/, voir config/urls.py.)
"""
from django.urls import path

from .views import ClientReviewsView, WorkerReviewsView

urlpatterns = [
    path("workers/<int:profile_id>/", WorkerReviewsView.as_view(), name="reviews-worker"),
    path("clients/<int:profile_id>/", ClientReviewsView.as_view(), name="reviews-client"),
]
