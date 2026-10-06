"""
Vues (endpoints) de l'app notifications.
"""
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, MESSAGE_ONLY, PAGINATION_PARAMETERS, paginated

from .serializers import MarkReadSerializer, NotificationSerializer


class NotificationListView(APIView):
    """GET /api/notifications/ — mes notifications, les plus récentes d'abord (20 par page)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Mes notifications",
        parameters=PAGINATION_PARAMETERS,
        responses={200: paginated("PaginatedNotifications", NotificationSerializer), **AUTH_ERRORS},
    )
    def get(self, request):
        return paginated_response(request, self, request.user.notifications.all(), NotificationSerializer)


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/ — nombre de notifications non lues (pastille de la cloche)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Nombre de notifications non lues",
        responses={
            200: inline_serializer(name="UnreadCount", fields={"unread": drf_serializers.IntegerField()}),
            **AUTH_ERRORS,
        },
    )
    def get(self, request):
        return Response({"unread": request.user.notifications.filter(read_at__isnull=True).count()})


class MarkReadView(APIView):
    """POST /api/notifications/read/ — marquer comme lues (toutes, ou celles de `ids`)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notifications"],
        summary="Marquer mes notifications comme lues",
        request=MarkReadSerializer,
        responses={200: MESSAGE_ONLY, **AUTH_ERRORS},
    )
    def post(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        unread = request.user.notifications.filter(read_at__isnull=True)
        if "ids" in serializer.validated_data:
            unread = unread.filter(id__in=serializer.validated_data["ids"])
        unread.update(read_at=timezone.now())
        return Response({"message": "Notifications lues."})
