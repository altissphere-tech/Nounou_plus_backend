"""
Vues (endpoints) de l'app matching.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.workers.models import WorkerProfile
from common.pagination import paginated_response
from common.permissions import IsWorkerOrClient

from .models import Match
from .serializers import InterestSerializer, MatchSerializer

NO_PROFILE_MESSAGE = "Vous devez d'abord créer votre profil avant de manifester un intérêt."
UNVERIFIED_WORKER_MESSAGE = (
    "Votre profil doit être vérifié par l'équipe NOUNOU+ avant de pouvoir contacter des clients."
)


def interest_response(request, match, created):
    """Enregistre l'intérêt de l'utilisateur sur ce match et construit la réponse de l'API."""
    match.set_decision(request.user, Match.DECISION_INTERESTED)
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

    def post(self, request, pk):
        match = get_object_or_404(Match.objects.for_user(request.user), pk=pk)
        match.set_decision(request.user, Match.DECISION_DECLINED)
        return Response(
            {
                "message": "Mise en relation refusée.",
                "match": MatchSerializer(match, context={"request": request}).data,
            }
        )
