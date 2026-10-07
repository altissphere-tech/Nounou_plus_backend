"""
Routes de l'app notifications, montées sous /api/notifications/.
"""
from django.urls import path

from .views import MarkReadView, NotificationListView, UnreadCountView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("unread-count/", UnreadCountView.as_view(), name="notifications-unread-count"),
    path("read/", MarkReadView.as_view(), name="notifications-read"),
]
