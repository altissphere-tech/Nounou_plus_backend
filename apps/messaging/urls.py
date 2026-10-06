"""
Routes de l'app messaging.
Montées sous le préfixe /api/matches/<match_id>/messages/ dans config/urls.py.
"""
from django.urls import path

from .views import ConversationView

urlpatterns = [
    path("", ConversationView.as_view(), name="messages-conversation"),
]
