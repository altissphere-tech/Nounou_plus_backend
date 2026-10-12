"""
Vues (endpoints) de l'app reviews.
"""
from django.conf import settings
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import ClientProfile
from apps.matching.models import Match
from apps.workers.models import WorkerProfile
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message
from common.permissions import IsWorkerOrClient

from .models import CLIENT_CRITERIA, WORKER_CRITERIA, Review, rating_summary
from .serializers import ReviewCreateSerializer, ReviewSerializer


# Résumé des notes, commun aux avis des travailleurs et des clients
REVIEW_SUMMARY = inline_serializer(
    name="ReviewSummary",
    fields={
        "average": drf_serializers.CharField(allow_null=True, help_text="Moyenne sur 5, ex : \"4.5\"."),
        "count": drf_serializers.IntegerField(help_text="Nombre d'avis."),
        "criteria": drf_serializers.DictField(
            child=drf_serializers.FloatField(allow_null=True),
            help_text="Moyenne par critère.",
        ),
    },
)


class MatchReviewView(APIView):
    """
    POST /api/matches/<match_id>/review/

    Évalue l'autre partie d'une mise en relation.
    - Client → travailleur : { "punctuality": 5, "competence": 4, "reliability": 5, "comment": "…" }
    - Travailleur → client : { "respect": 5, "clarity": 4, "payment_on_time": 5, "comment": "…" }
    Possible une seule fois, à partir de 7 jours après le premier match mutuel.
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Évaluations"],
        summary="Évaluer l'autre personne d'une mise en relation",
        description="Une seule fois, à partir de 7 jours après le premier match mutuel.\n\n"
        "- Client → travailleur : `punctuality`, `competence`, `reliability` (1 à 5)\n"
        "- Travailleur → client : `respect`, `clarity`, `payment_on_time` (1 à 5)\n\n"
        "`comment` est facultatif.",
        request=ReviewCreateSerializer,
        responses={
            201: with_message("ReviewCreated", "review", ReviewSerializer),
            400: error("Notes manquantes ou invalides, ou évaluation déjà faite."),
            401: AUTH_ERRORS[401],
            403: error("Trop tôt (période d'essai), ou jamais de match mutuel."),
            404: error("Mise en relation introuvable."),
        },
    )
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
                detail = (
                    "L'évaluation n'est possible qu'après un match mutuel resté actif "
                    f"au moins {settings.REVIEW_DELAY_DAYS} jours."
                )
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


def _reviews_response(request, view, user, criteria):
    """Résumé (moyennes) + liste paginée des évaluations reçues par un utilisateur."""
    reviews = user.reviews_received.select_related(
        "author__client_profile", "author__worker_profile"
    )
    averages = reviews.aggregate(**{name: Avg(name) for name in criteria})
    summary = {
        **rating_summary(user),
        "criteria": {
            name: round(value, 1) if value is not None else None
            for name, value in averages.items()
        },
    }
    return paginated_response(request, view, reviews, ReviewSerializer, extra={"summary": summary})


class WorkerReviewsView(APIView):
    """
    GET /api/reviews/workers/<profile_id>/

    Évaluations reçues par un travailleur (moyennes par critère + commentaires).
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Évaluations"],
        summary="Avis reçus par un travailleur",
        parameters=PAGINATION_PARAMETERS,
        responses={
            200: paginated("PaginatedWorkerReviews", ReviewSerializer, extra_fields={"summary": REVIEW_SUMMARY}),
            404: error("Profil introuvable."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request, profile_id):
        # Comme la fiche du travailleur : seulement les profils vérifiés et actifs
        worker = get_object_or_404(WorkerProfile.objects.visible_to_clients().select_related("user"), pk=profile_id)
        return _reviews_response(request, self, worker.user, WORKER_CRITERIA)


class ClientReviewsView(APIView):
    """
    GET /api/reviews/clients/<profile_id>/

    Évaluations reçues par un client (moyennes par critère + commentaires).
    Réservé aux travailleurs vérifiés (comme la liste des familles) et à la famille elle-même.
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Évaluations"],
        summary="Avis reçus par un client",
        parameters=PAGINATION_PARAMETERS,
        responses={
            200: paginated("PaginatedClientReviews", ReviewSerializer, extra_fields={"summary": REVIEW_SUMMARY}),
            404: error("Profil introuvable."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request, profile_id):
        # Comme la liste des familles : visibles par les travailleurs vérifiés, et par la
        # famille elle-même. Les autres reçoivent 404 (pas d'indice sur les profils existants).
        visible = ClientProfile.objects.active().select_related("user")
        worker = getattr(request.user, "worker_profile", None)
        if worker is None or not worker.is_verified:
            visible = visible.filter(user=request.user)
        client = get_object_or_404(visible, pk=profile_id)
        return _reviews_response(request, self, client.user, CLIENT_CRITERIA)
