"""
Vues (endpoints) de l'app messaging.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification, display_name, notify

from apps.matching.models import Match
from common.permissions import IsWorkerOrClient
from common.schema import AUTH_ERRORS, error

from .models import Message
from .serializers import MessageCreateSerializer, MessageSerializer

CLOSED_MESSAGE = "La messagerie n'est disponible qu'après un match mutuel."


class ConversationView(APIView):
    """
    GET  /api/matches/<match_id>/messages/ → lire la conversation
    POST /api/matches/<match_id>/messages/ → envoyer un message  { "content": "Bonjour" }

    Réservé aux deux participants d'un match mutuel.
    La lecture marque comme lus les messages reçus.
    """

    permission_classes = [IsWorkerOrClient]

    def _get_open_match(self, request, match_id):
        """Retourne le match si l'utilisateur y participe et qu'il est mutuel, sinon une erreur."""
        match = get_object_or_404(Match.objects.for_user(request.user), pk=match_id)
        if match.status_seen_by(request.user) != Match.STATUS_MUTUAL:
            return match, Response({"detail": CLOSED_MESSAGE}, status=status.HTTP_403_FORBIDDEN)
        return match, None

    @extend_schema(
        tags=["Messagerie"],
        summary="Lire la conversation",
        description="Les messages reçus sont marqués comme lus.",
        responses={
            200: inline_serializer(
                name="Conversation",
                fields={
                    "count": drf_serializers.IntegerField(),
                    "results": MessageSerializer(many=True),
                },
            ),
            403: error("Messagerie fermée : le match n'est pas (ou plus) mutuel."),
            404: error("Mise en relation introuvable."),
            401: AUTH_ERRORS[401],
        },
    )
    def get(self, request, match_id):
        match, error = self._get_open_match(request, match_id)
        if error:
            return error
        # Marque comme lus les messages reçus
        match.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
            read_at=timezone.now()
        )
        messages = match.messages.all()
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return Response({"count": len(serializer.data), "results": serializer.data})

    @extend_schema(
        tags=["Messagerie"],
        summary="Envoyer un message",
        request=MessageCreateSerializer,
        responses={
            201: MessageSerializer,
            400: error("Message vide ou trop long (2000 caractères maximum)."),
            403: error("Messagerie fermée : le match n'est pas (ou plus) mutuel."),
            404: error("Mise en relation introuvable."),
            401: AUTH_ERRORS[401],
        },
    )
    def post(self, request, match_id):
        match, error = self._get_open_match(request, match_id)
        if error:
            return error
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = Message.objects.create(
            match=match,
            sender=request.user,
            content=serializer.validated_data["content"],
        )
        client_side = match.is_client_side(request.user)
        me, other = (match.client, match.worker) if client_side else (match.worker, match.client)
        notify(other.user, Notification.KIND_MESSAGE, match_id=match.id, name=display_name(me, full=True))
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
