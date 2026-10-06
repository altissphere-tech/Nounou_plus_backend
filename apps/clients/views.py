"""
Vues (endpoints) de l'app clients.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsClient, IsWorker

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

    def get(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil client."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ClientProfileSerializer(profile).data)

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
    manifester leur intérêt. Le nom de famille est réduit à son initiale et
    le téléphone n'est jamais inclus (révélés uniquement après un match mutuel).
    """

    permission_classes = [IsWorker]

    def get(self, request):
        profiles = ClientProfile.objects.prefetch_related("services_needed")
        serializer = ClientProfilePublicSerializer(profiles, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})
