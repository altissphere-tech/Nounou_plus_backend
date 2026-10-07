"""
Routes de l'app favoris, montées sous /api/favorites/.
"""
from django.urls import path

from .views import FavoriteJobView, FavoriteListView, FavoriteWorkerView

urlpatterns = [
    path("", FavoriteListView.as_view(), name="favorites-list"),
    path("workers/<int:pk>/", FavoriteWorkerView.as_view(), name="favorites-worker"),
    path("jobs/<int:pk>/", FavoriteJobView.as_view(), name="favorites-job"),
]
