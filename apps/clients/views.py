"""
Vues (endpoints) de l'app clients.
"""
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common import choices
from common.filters import get_choice, get_decimal, get_text
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message
from common.permissions import IsClient, IsVerifiedWorker

from .models import ClientProfile
from .serializers import (
    ClientProfilePublicSerializer,
    ClientProfileSerializer,
    ClientProfileWriteSerializer,
)


class ClientProfileCreateView(APIView):
    """
    POST /api/clients/profile/

    Crée le profil du client connecté.
    - Réservé aux utilisateurs avec le rôle "client".
    - Un client ne peut créer qu'un seul profil.
    """

    permission_classes = [IsClient]

    @extend_schema(
        tags=["Clients"],
        summary="Créer mon profil client",
        request=ClientProfileWriteSerializer,
        responses={
            201: with_message("ClientProfileCreated", "profile", ClientProfileSerializer),
            400: error("Données invalides, ou profil déjà existant."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request):
        if hasattr(request.user, "client_profile"):
            return Response(
                {"detail": "Vous avez déjà un profil client."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ClientProfileWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(
            {
                "message": "Profil créé avec succès.",
                "profile": ClientProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ClientProfileMeView(APIView):
    """
    GET   /api/clients/profile/me/ → voir son propre profil
    PATCH /api/clients/profile/me/ → modifier son propre profil

    Réservé au client connecté propriétaire du profil.
    """

    permission_classes = [IsClient]

    def _get_profile(self, user):
        """Récupère le profil ou retourne None."""
        try:
            return user.client_profile
        except ClientProfile.DoesNotExist:
            return None

    @extend_schema(
        tags=["Clients"],
        summary="Voir mon profil client",
        responses={200: ClientProfileSerializer, 404: error("Profil pas encore créé."), **AUTH_ERRORS},
    )
    def get(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil client."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ClientProfileSerializer(profile).data)

    @extend_schema(
        tags=["Clients"],
        summary="Modifier mon profil client",
        request=ClientProfileWriteSerializer,
        responses={
            200: with_message("ClientProfileUpdated", "profile", ClientProfileSerializer),
            400: error("Données invalides."),
            404: error("Profil pas encore créé."),
            **AUTH_ERRORS,
        },
    )
    def patch(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil client."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ClientProfileWriteSerializer(
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
                "profile": ClientProfileSerializer(profile).data,
            }
        )


class ClientProfileListView(APIView):
    """
    GET /api/clients/

    Liste des besoins des clients, consultable par les travailleurs pour
    manifester leur intérêt, par pages de 20 (les plus récents d'abord).
    Le nom de famille est réduit à son initiale et le téléphone n'est jamais
    inclus (révélés uniquement après un match mutuel).

    Filtres (tous facultatifs) :
    - service=nounou            → recherche ce service
    - location=golf             → quartier contenant ce texte
    - availability=temps_plein  → disponibilité recherchée exacte
    - min_budget=150            → budget supérieur ou égal (exclut les budgets non renseignés)
    """

    permission_classes = [IsVerifiedWorker]  # familles visibles des travailleurs vérifiés seulement

    @extend_schema(
        tags=["Clients"],
        summary="Rechercher des besoins clients (travailleurs)",
        operation_id="clients_list",
        parameters=[
            OpenApiParameter("service", str, description="Service recherché : nounou, menage ou cuisine."),
            OpenApiParameter("location", str, description="Quartier contenant ce texte."),
            OpenApiParameter(
                "availability", str, enum=[c[0] for c in choices.AVAILABILITY_CHOICES],
                description="Disponibilité recherchée.",
            ),
            OpenApiParameter("min_budget", float, description="Budget minimum (exclut les budgets non renseignés)."),
            *PAGINATION_PARAMETERS,
        ],
        responses={
            200: paginated("PaginatedClientProfiles", ClientProfilePublicSerializer),
            400: error("Valeur de filtre invalide."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request):
        profiles = ClientProfile.objects.active().select_related("user")

        service = get_text(request, "service")
        if service:
            profiles = profiles.filter(services_needed__slug=service)
        location = get_text(request, "location")
        if location:
            profiles = profiles.filter(location__icontains=location)
        availability = get_choice(request, "availability", choices.AVAILABILITY_CHOICES)
        if availability:
            profiles = profiles.filter(availability_needed=availability)
        min_budget = get_decimal(request, "min_budget")
        if min_budget is not None:
            profiles = profiles.filter(budget__gte=min_budget)

        profiles = profiles.distinct().order_by("-created_at").prefetch_related("services_needed")
        return paginated_response(request, self, profiles, ClientProfilePublicSerializer)
