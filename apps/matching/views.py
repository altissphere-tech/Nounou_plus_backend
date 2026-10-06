"""
Vues (endpoints) de l'app matching.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.workers.models import WorkerProfile
from common.permissions import IsWorkerOrClient

from .models import Match
from .serializers import InterestSerializer, MatchSerializer

NO_PROFILE_MESSAGE = "Vous devez d'abord créer votre profil avant de manifester un intérêt."


def _own_profile(user):
    """Retourne le profil (client ou travailleur) de l'utilisateur, ou None."""
    attr = "client_profile" if user.role == User.ROLE_CLIENT else "worker_profile"
    return getattr(user, attr, None)


def _user_matches(user):
    """Tous les matchs auxquels l'utilisateur participe."""
    return Match.objects.filter(
        Q(client__user=user) | Q(worker__user=user)
    ).select_related("client__user", "worker__user")


class MatchListView(APIView):
    """
    GET /api/matches/

    Liste des mises en relation de l'utilisateur connecté (client ou travailleur) :
    intérêts envoyés, intérêts reçus, matchs mutuels et refus faits par soi.
    """

    permission_classes = [IsWorkerOrClient]

    def get(self, request):
        matches = _user_matches(request.user).prefetch_related(
            "client__services_needed", "worker__services"
        )
        serializer = MatchSerializer(matches, many=True, context={"request": request})
        return Response({"count": len(serializer.data), "results": serializer.data})


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
            worker = get_object_or_404(WorkerProfile, pk=profile_id, is_verified=True)
            match, created = Match.objects.get_or_create(client=own_profile, worker=worker)
        else:
            if not own_profile.is_verified:
                return Response(
                    {"detail": "Votre profil doit être vérifié par l'équipe NOUNOU+ "
                               "avant de pouvoir contacter des clients."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            client = get_object_or_404(ClientProfile, pk=profile_id)
            match, created = Match.objects.get_or_create(client=client, worker=own_profile)

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


class MatchDeclineView(APIView):
    """
    POST /api/matches/<id>/decline/

    Refuse une mise en relation. L'autre personne n'en est jamais informée :
    pour elle, la demande reste « en attente ».
    """

    permission_classes = [IsWorkerOrClient]

    def post(self, request, pk):
        match = get_object_or_404(_user_matches(request.user), pk=pk)
        match.set_decision(request.user, Match.DECISION_DECLINED)
        return Response(
            {
                "message": "Mise en relation refusée.",
                "match": MatchSerializer(match, context={"request": request}).data,
            }
        )
