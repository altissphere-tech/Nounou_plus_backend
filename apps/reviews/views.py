"""
Vues (endpoints) de l'app reviews.
"""
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import ClientProfile
from apps.matching.models import Match
from apps.workers.models import WorkerProfile
from common.permissions import IsWorkerOrClient

from .models import CLIENT_CRITERIA, WORKER_CRITERIA, Review, rating_summary
from .serializers import ReviewCreateSerializer, ReviewSerializer


class MatchReviewView(APIView):
    """
    POST /api/matches/<match_id>/review/

    Évalue l'autre partie d'une mise en relation.
    - Client → travailleur : { "punctuality": 5, "competence": 4, "reliability": 5, "comment": "…" }
    - Travailleur → client : { "respect": 5, "clarity": 4, "payment_on_time": 5, "comment": "…" }
    Possible une seule fois, à partir de 7 jours après le premier match mutuel.
    """

    permission_classes = [IsWorkerOrClient]

    def post(self, request, match_id):
        match = get_object_or_404(Match.objects.for_user(request.user), pk=match_id)

        if match.reviews.filter(author=request.user).exists():
            return Response(
                {"detail": "Vous avez déjà évalué cette personne."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not match.can_be_reviewed_by(request.user):
            available_at = match.review_available_at
            if available_at is None:
                detail = "L'évaluation n'est possible qu'après un match mutuel."
            else:
                detail = (
                    "L'évaluation sera possible à partir du "
                    f"{available_at.strftime('%d/%m/%Y')}, après la période d'essai."
                )
            return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)

        target_is_worker = match.is_client_side(request.user)
        serializer = ReviewCreateSerializer(
            data=request.data, context={"target_is_worker": target_is_worker}
        )
        serializer.is_valid(raise_exception=True)
        target = match.worker.user if target_is_worker else match.client.user
        review = Review.objects.create(
            match=match, author=request.user, target=target, **serializer.validated_data
        )
        return Response(
            {"message": "Merci pour votre évaluation.", "review": ReviewSerializer(review).data},
            status=status.HTTP_201_CREATED,
        )


def _reviews_response(user, criteria):
    """Résumé (moyennes) + liste des évaluations reçues par un utilisateur."""
    reviews = user.reviews_received.select_related(
        "author__client_profile", "author__worker_profile"
    )
    averages = reviews.aggregate(**{name: Avg(name) for name in criteria})
    return Response(
        {
            "summary": {
                **rating_summary(user),
                "criteria": {
                    name: round(value, 1) if value is not None else None
                    for name, value in averages.items()
                },
            },
            "results": ReviewSerializer(reviews, many=True).data,
        }
    )


class WorkerReviewsView(APIView):
    """
    GET /api/reviews/workers/<profile_id>/

    Évaluations reçues par un travailleur (moyennes par critère + commentaires).
    """

    permission_classes = [IsWorkerOrClient]

    def get(self, request, profile_id):
        worker = get_object_or_404(WorkerProfile.objects.active().select_related("user"), pk=profile_id)
        return _reviews_response(worker.user, WORKER_CRITERIA)


class ClientReviewsView(APIView):
    """
    GET /api/reviews/clients/<profile_id>/

    Évaluations reçues par un client (moyennes par critère + commentaires).
    """

    permission_classes = [IsWorkerOrClient]

    def get(self, request, profile_id):
        client = get_object_or_404(ClientProfile.objects.active().select_related("user"), pk=profile_id)
        return _reviews_response(client.user, CLIENT_CRITERIA)
