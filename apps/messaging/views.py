"""
Vues (endpoints) de l'app messaging.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matching.models import Match
from common.permissions import IsWorkerOrClient

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
        match = get_object_or_404(
            Match.objects.filter(Q(client__user=request.user) | Q(worker__user=request.user)),
            pk=match_id,
        )
        if match.status_seen_by(request.user) != Match.STATUS_MUTUAL:
            return match, Response({"detail": CLOSED_MESSAGE}, status=status.HTTP_403_FORBIDDEN)
        return match, None

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
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
