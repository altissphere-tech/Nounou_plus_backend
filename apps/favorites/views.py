"""
Vues (endpoints) de l'app favoris.

Les favoris suivent les mêmes règles de visibilité que les listes : un profil
qui n'est plus vérifié (ou suspendu) et une annonce fermée disparaissent des favoris.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.jobs.models import JobRequest
from apps.jobs.serializers import JobRequestPublicSerializer
from apps.workers.models import WorkerProfile
from apps.workers.serializers import WorkerProfilePublicSerializer
from common.permissions import IsClient, IsWorker, IsWorkerOrClient
from common.schema import AUTH_ERRORS, MESSAGE_ONLY, error

from .models import FavoriteJob, FavoriteWorker


class FavoriteListView(APIView):
    """
    GET /api/favorites/

    Famille : ses travailleurs favoris (`workers`). Travailleur : ses annonces favorites (`jobs`).
    """

    permission_classes = [IsWorkerOrClient]

    @extend_schema(
        tags=["Favoris"],
        summary="Mes favoris",
        responses={
            200: inline_serializer(
                name="Favorites",
                fields={
                    "workers": WorkerProfilePublicSerializer(many=True),
                    "jobs": JobRequestPublicSerializer(many=True),
                },
            ),
            **AUTH_ERRORS,
        },
    )
    def get(self, request):
        workers, jobs = [], []
        if request.user.role == User.ROLE_CLIENT:
            workers = WorkerProfile.objects.visible_to_clients().filter(
                favorited_by__user=request.user
            ).order_by("-favorited_by__created_at").select_related("user").prefetch_related("services")
        else:
            jobs = JobRequest.objects.open_to_workers().filter(
                favorited_by__user=request.user
            ).order_by("-favorited_by__created_at").select_related("client__user", "service")
        return Response(
            {
                "workers": WorkerProfilePublicSerializer(workers, many=True).data,
                "jobs": JobRequestPublicSerializer(jobs, many=True).data,
            }
        )


class FavoriteWorkerView(APIView):
    """PUT / DELETE /api/favorites/workers/<id>/ — ajouter ou retirer un travailleur (familles)."""

    permission_classes = [IsClient]

    @extend_schema(
        tags=["Favoris"],
        summary="Ajouter un travailleur à mes favoris",
        request=None,
        responses={200: MESSAGE_ONLY, 404: error("Profil introuvable."), **AUTH_ERRORS},
    )
    def put(self, request, pk):
        worker = get_object_or_404(WorkerProfile.objects.visible_to_clients(), pk=pk)
        FavoriteWorker.objects.get_or_create(user=request.user, worker=worker)
        return Response({"message": "Ajouté à vos favoris."})

    @extend_schema(
        tags=["Favoris"], summary="Retirer un travailleur de mes favoris", responses={200: MESSAGE_ONLY, **AUTH_ERRORS}
    )
    def delete(self, request, pk):
        FavoriteWorker.objects.filter(user=request.user, worker_id=pk).delete()
        return Response({"message": "Retiré de vos favoris."})


class FavoriteJobView(APIView):
    """PUT / DELETE /api/favorites/jobs/<id>/ — ajouter ou retirer une annonce (travailleurs)."""

    permission_classes = [IsWorker]

    @extend_schema(
        tags=["Favoris"],
        summary="Ajouter une annonce à mes favoris",
        request=None,
        responses={200: MESSAGE_ONLY, 404: error("Annonce introuvable ou fermée."), **AUTH_ERRORS},
    )
    def put(self, request, pk):
        job = get_object_or_404(JobRequest.objects.open_to_workers(), pk=pk)
        FavoriteJob.objects.get_or_create(user=request.user, job=job)
        return Response({"message": "Ajoutée à vos favoris."})

    @extend_schema(
        tags=["Favoris"], summary="Retirer une annonce de mes favoris", responses={200: MESSAGE_ONLY, **AUTH_ERRORS}
    )
    def delete(self, request, pk):
        FavoriteJob.objects.filter(user=request.user, job_id=pk).delete()
        return Response({"message": "Retirée de vos favoris."})
