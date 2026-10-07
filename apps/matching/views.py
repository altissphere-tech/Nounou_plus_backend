"""
Vues (endpoints) de l'app matching.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.notifications.models import Notification, display_name, notify
from apps.workers.models import WorkerProfile
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message
from common.permissions import IsWorkerOrClient

from .models import Match
from .serializers import InterestSerializer, MatchSerializer

NO_PROFILE_MESSAGE = "Vous devez d'abord créer votre profil avant de manifester un intérêt."
UNVERIFIED_WORKER_MESSAGE = (
    "Votre profil doit être vérifié par l'équipe NOUNOU+ avant de pouvoir contacter des clients."
)


# Format de réponse commun à « manifester son intérêt » (profil ou annonce)
_INTEREST_RESPONSE = with_message("InterestResponse", "match", MatchSerializer)
INTEREST_RESPONSES = {200: _INTEREST_RESPONSE, 201: _INTEREST_RESPONSE}


def _notify_interest(match, user, was_mutual: bool) -> None:
    """
    Prévient l'autre personne : « intérêt reçu » ou « c'est un match ».
    Rien n'est envoyé à quelqu'un qui a déjà refusé (son refus reste discret).
    """
    client_side = match.is_client_side(user)
    me, other = (match.client, match.worker) if client_side else (match.worker, match.client)
    if match.is_mutual and not was_mutual:
        notify(other.user, Notification.KIND_MATCH, match_id=match.id, name=display_name(me, full=True))
    elif not match.is_mutual and match.decision_of(other.user) == Match.DECISION_PENDING:
        notify(other.user, Notification.KIND_INTEREST, match_id=match.id, name=display_name(me, full=False))


def interest_response(request, match, created):
    """Enregistre l'intérêt de l'utilisateur sur ce match et construit la réponse de l'API."""
    already_interested = match.decision_of(request.user) == Match.DECISION_INTERESTED
    was_mutual = match.is_mutual
    match.set_decision(request.user, Match.DECISION_INTERESTED)
    if not already_interested:
        _notify_interest(match, request.user, was_mutual)
    if match.is_mutual:
        message = "C'est un match ! Vous pouvez maintenant voir les coordonnées de l'autre personne."
    else:
        message = "Votre intérêt a été enregistré."
    return Response(
        {
            "message": message,
            "match": MatchSerializer(match, context={"request": request}).data,
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


def _own_profile(user):
    """Retourne le profil (client ou travailleur) de l'utilisateur, ou None."""
    attr = "client_profile" if user.role == User.ROLE_CLIENT else "worker_profile"
    return getattr(user, attr, None)


class MatchListView(APIView):
    """
    GET /api/matches/

    Liste des mises en relation de l'utilisateur connecté (client ou travailleur) :
    intérêts envoyés, intérêts reçus, matchs mutuels et refus faits par soi.
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Mise en relation"],
        summary="Mes mises en relation",
        operation_id="matches_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: paginated("PaginatedMatches", MatchSerializer), **AUTH_ERRORS},
    )
    def get(self, request):
        matches = Match.objects.for_user(request.user).prefetch_related(
            "client__services_needed", "worker__services"
        )
        return paginated_response(
            request, self, matches, MatchSerializer, context={"request": request}
        )


class MatchInterestView(APIView):
    """
    POST /api/matches/interest/   { "profile_id": 12 }

    Manifeste son intérêt pour un profil :
    - un client choisit un profil travailleur (vérifié uniquement) ;
    - un travailleur choisit un profil client.
    Si l'autre partie était déjà intéressée, le match devient mutuel.
    Sert aussi à accepter un intérêt reçu, ou à revenir sur un refus.
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Mise en relation"],
        summary="Me déclarer intéressé(e) par un profil",
        description="Client → `profile_id` d'un travailleur vérifié ; travailleur → `profile_id` "
        "d'un client. Si l'autre était déjà intéressé, le match devient mutuel (statut `mutuel`) : "
        "nom complet et téléphone apparaissent dans `other_party`. 201 si la mise en relation est "
        "nouvelle, 200 sinon.",
        request=InterestSerializer,
        responses={
            **INTEREST_RESPONSES,
            400: error("Vous n'avez pas encore créé votre profil."),
            401: AUTH_ERRORS[401],
            403: error("Rôle non autorisé, ou travailleur pas encore vérifié."),
            404: error("Profil introuvable ou non visible."),
        },
    )
    def post(self, request):
        serializer = InterestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile_id = serializer.validated_data["profile_id"]

        own_profile = _own_profile(request.user)
        if own_profile is None:
            return Response({"detail": NO_PROFILE_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == User.ROLE_CLIENT:
            # Les clients ne voient que les travailleurs vérifiés
            worker = get_object_or_404(WorkerProfile.objects.visible_to_clients(), pk=profile_id)
            match, created = Match.objects.get_or_create(client=own_profile, worker=worker)
        else:
            if not own_profile.is_verified:
                return Response(
                    {"detail": UNVERIFIED_WORKER_MESSAGE}, status=status.HTTP_403_FORBIDDEN
                )
            client = get_object_or_404(ClientProfile.objects.active(), pk=profile_id)
            match, created = Match.objects.get_or_create(client=client, worker=own_profile)

        return interest_response(request, match, created)


class MatchDeclineView(APIView):
    """
    POST /api/matches/<id>/decline/

    Refuse une mise en relation. L'autre personne n'en est jamais informée :
    pour elle, la demande reste « en attente ».
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Mise en relation"],
        summary="Refuser une mise en relation",
        description="L'autre personne n'en est jamais informée : pour elle, la demande reste « en attente ».",
        request=None,
        responses={
            200: with_message("MatchDeclined", "match", MatchSerializer),
            404: error("Mise en relation introuvable."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request, pk):
        match = get_object_or_404(Match.objects.for_user(request.user), pk=pk)
        match.set_decision(request.user, Match.DECISION_DECLINED)
        return Response(
            {
                "message": "Mise en relation refusée.",
                "match": MatchSerializer(match, context={"request": request}).data,
            }
        )
