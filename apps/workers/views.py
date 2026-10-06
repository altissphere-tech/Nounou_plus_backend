"""
Vues (endpoints) de l'app workers.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

    def get(self, request):
        profile = self._get_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Vous n'avez pas encore créé de profil travailleur."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(WorkerProfileSerializer(profile).data)

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

    Liste en lecture seule des profils travailleurs vérifiés (is_verified=True).
    Accessible aux clients ET aux travailleurs authentifiés.

    Les numéros de téléphone sont masqués et le nom de famille réduit à son initiale.
    Pas de recherche avancée en V1 — uniquement un tri par date de création.
    """

    permission_classes = [IsWorkerOrClient]

    def get(self, request):
        profiles = WorkerProfile.objects.visible_to_clients().select_related("user")
        serializer = WorkerProfilePublicSerializer(profiles, many=True)
        return Response(
            {
                "count": profiles.count(),
                "results": serializer.data,
            }
        )
