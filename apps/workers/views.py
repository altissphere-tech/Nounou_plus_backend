"""
Vues (endpoints) de l'app workers.
"""
from django.db.models import Avg, F
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common import choices
from common.filters import get_choice, get_decimal, get_int, get_text
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message

from .models import WorkerProfile
from .permissions import IsWorker, IsWorkerOrClient
from .serializers import (
    WorkerProfilePublicSerializer,
    WorkerProfileSerializer,
    WorkerProfileWriteSerializer,
)


class WorkerProfileCreateView(APIView):
    """
    POST /api/workers/profile/

    Crée le profil professionnel du travailleur connecté.
    - Réservé aux utilisateurs avec le rôle "travailleur".
    - Un travailleur ne peut créer qu'un seul profil.
    """

    permission_classes = [IsWorker]

    @extend_schema(
        tags=["Travailleurs"],
        summary="Créer mon profil travailleur",
        request=WorkerProfileWriteSerializer,
        responses={
            201: with_message("WorkerProfileCreated", "profile", WorkerProfileSerializer),
            400: error("Données invalides, ou profil déjà existant."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request):
        # Vérifier qu'un profil n'existe pas déjà
        if hasattr(request.user, "worker_profile"):
            return Response(
                {"detail": "Vous avez déjà un profil travailleur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WorkerProfileWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            {
                "message": "Profil créé avec succès.",
                "profile": WorkerProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )


class WorkerProfileMeView(APIView):
    """
    GET  /api/workers/profile/me/  → voir son propre profil complet
    PATCH /api/workers/profile/me/ → modifier son propre profil

    Réservé au travailleur connecté propriétaire du profil.
    """

    permission_classes = [IsWorker]

    def _get_profile(self, user):
        """Récupère le profil ou retourne None."""
        try:
            return user.worker_profile
        except WorkerProfile.DoesNotExist:
            return None

    @extend_schema(
        tags=["Travailleurs"],
        summary="Voir mon profil travailleur",
        responses={200: WorkerProfileSerializer, 404: error("Profil pas encore créé."), **AUTH_ERRORS},
    )
    def get(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil travailleur."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(WorkerProfileSerializer(profile).data)

    @extend_schema(
        tags=["Travailleurs"],
        summary="Modifier mon profil travailleur",
        request=WorkerProfileWriteSerializer,
        responses={
            200: with_message("WorkerProfileUpdated", "profile", WorkerProfileSerializer),
            400: error("Données invalides."),
            404: error("Profil pas encore créé."),
            **AUTH_ERRORS,
        },
    )
    def patch(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil travailleur."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorkerProfileWriteSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            {
                "message": "Profil mis à jour.",
                "profile": WorkerProfileSerializer(profile).data,
            }
        )


class WorkerProfileListView(APIView):
    """
    GET /api/workers/

    Recherche parmi les profils travailleurs vérifiés, par pages de 20.
    Accessible aux clients ET aux travailleurs authentifiés.
    Les numéros de téléphone sont masqués et le nom de famille réduit à son initiale.

    Filtres (tous facultatifs) :
    - service=nounou            → propose ce service (nounou, menage, cuisine)
    - location=kenya            → quartier contenant ce texte (majuscules ignorées)
    - availability=temps_plein  → disponibilité exacte
    - max_salary=200            → prétention salariale inférieure ou égale
    - min_experience=2          → au moins 2 ans d'expérience

    Tri : ordering=recent (défaut) | salary | experience | rating
    """

    permission_classes = [IsWorkerOrClient]

    ORDERINGS = {
        "recent": ["-created_at"],
        "salary": ["expected_salary", "-created_at"],
        "experience": ["-years_experience", "-created_at"],
        "rating": [F("average_rating").desc(nulls_last=True), "-created_at"],
    }

    @extend_schema(
        tags=["Travailleurs"],
        summary="Rechercher des travailleurs vérifiés",
        operation_id="workers_list",
        parameters=[
            OpenApiParameter("service", str, description="Service proposé : nounou, menage ou cuisine."),
            OpenApiParameter("location", str, description="Quartier contenant ce texte (ex : kenya)."),
            OpenApiParameter(
                "availability", str, enum=[c[0] for c in choices.AVAILABILITY_CHOICES],
                description="Disponibilité exacte.",
            ),
            OpenApiParameter("max_salary", float, description="Prétention salariale maximale."),
            OpenApiParameter("min_experience", int, description="Années d'expérience minimum."),
            OpenApiParameter(
                "ordering", str, enum=["recent", "salary", "experience", "rating"],
                description="Tri (par défaut : recent).",
            ),
            *PAGINATION_PARAMETERS,
        ],
        responses={
            200: paginated("PaginatedWorkerProfiles", WorkerProfilePublicSerializer),
            400: error("Valeur de filtre invalide."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request):
        profiles = WorkerProfile.objects.visible_to_clients().select_related("user")

        service = get_text(request, "service")
        if service:
            profiles = profiles.filter(services__slug=service)
        location = get_text(request, "location")
        if location:
            profiles = profiles.filter(location__icontains=location)
        availability = get_choice(request, "availability", choices.AVAILABILITY_CHOICES)
        if availability:
            profiles = profiles.filter(availability=availability)
        max_salary = get_decimal(request, "max_salary")
        if max_salary is not None:
            profiles = profiles.filter(expected_salary__lte=max_salary)
        min_experience = get_int(request, "min_experience")
        if min_experience is not None:
            profiles = profiles.filter(years_experience__gte=min_experience)

        ordering = get_choice(
            request, "ordering", [(key, key) for key in self.ORDERINGS]
        ) or "recent"
        if ordering == "rating":
            profiles = profiles.annotate(average_rating=Avg("user__reviews_received__overall"))
        profiles = profiles.distinct().order_by(*self.ORDERINGS[ordering])

        return paginated_response(
            request, self, profiles.prefetch_related("services"), WorkerProfilePublicSerializer
        )
