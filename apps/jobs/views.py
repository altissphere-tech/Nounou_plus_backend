"""
Vues (endpoints) de l'app jobs.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.matching.models import Match
from apps.matching.views import UNVERIFIED_WORKER_MESSAGE, interest_response
from common import choices
from common.filters import get_choice, get_decimal, get_text
from common.pagination import paginated_response
from common.permissions import IsClient, IsWorker, IsWorkerOrClient

from .models import JobRequest
from .serializers import JobRequestPublicSerializer, JobRequestSerializer, JobRequestWriteSerializer

NO_CLIENT_PROFILE = "Vous devez d'abord créer votre profil client."
NO_WORKER_PROFILE = "Vous devez d'abord créer votre profil travailleur."


class JobListCreateView(APIView):
    """
    GET  /api/jobs/ → (travailleurs) annonces ouvertes, par pages de 20
         Filtres : service, location, availability, min_budget
    POST /api/jobs/ → (clients) publier une annonce
         { "title": "…", "service": "nounou", "availability": "temps_plein",
           "budget": "200", "location": "Golf", "description": "…" }
    """

    def get_permissions(self):
        return [IsWorker()] if self.request.method == "GET" else [IsClient()]

    def get(self, request):
        jobs = JobRequest.objects.open_to_workers().select_related("client__user", "service")

        service = get_text(request, "service")
        if service:
            jobs = jobs.filter(service__slug=service)
        location = get_text(request, "location")
        if location:
            jobs = jobs.filter(location__icontains=location)
        availability = get_choice(request, "availability", choices.AVAILABILITY_CHOICES)
        if availability:
            jobs = jobs.filter(availability=availability)
        min_budget = get_decimal(request, "min_budget")
        if min_budget is not None:
            jobs = jobs.filter(budget__gte=min_budget)

        return paginated_response(request, self, jobs, JobRequestPublicSerializer)

    def post(self, request):
        client = getattr(request.user, "client_profile", None)
        if client is None:
            return Response({"detail": NO_CLIENT_PROFILE}, status=status.HTTP_400_BAD_REQUEST)
        serializer = JobRequestWriteSerializer(data=request.data, context={"client": client})
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(
            {"message": "Annonce publiée.", "job": JobRequestSerializer(job).data},
            status=status.HTTP_201_CREATED,
        )


class MyJobsView(APIView):
    """
    GET /api/jobs/mine/ → (clients) ses propres annonces, tous statuts confondus.
    """

    permission_classes = [IsClient]

    def get(self, request):
        client = getattr(request.user, "client_profile", None)
        if client is None:
            return Response({"detail": NO_CLIENT_PROFILE}, status=status.HTTP_404_NOT_FOUND)
        jobs = client.job_requests.select_related("service")
        return paginated_response(request, self, jobs, JobRequestSerializer)


class JobDetailView(APIView):
    """
    GET   /api/jobs/<id>/ → voir une annonce (travailleur : si ouverte ; client : si c'est la sienne)
    PATCH /api/jobs/<id>/ → (client propriétaire) modifier l'annonce ou changer son statut
          (« pourvue » ou « fermee » la retire de la liste des travailleurs)
    """

    permission_classes = [IsWorkerOrClient]

    def get(self, request, pk):
        if request.user.role == User.ROLE_CLIENT:
            job = get_object_or_404(JobRequest, pk=pk, client__user=request.user)
            return Response(JobRequestSerializer(job).data)
        job = get_object_or_404(JobRequest.objects.open_to_workers(), pk=pk)
        return Response(JobRequestPublicSerializer(job).data)

    def patch(self, request, pk):
        if request.user.role != User.ROLE_CLIENT:
            return Response(
                {"detail": "Seule la famille qui a publié l'annonce peut la modifier."},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = get_object_or_404(JobRequest, pk=pk, client__user=request.user)
        serializer = JobRequestWriteSerializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response({"message": "Annonce mise à jour.", "job": JobRequestSerializer(job).data})


class JobInterestView(APIView):
    """
    POST /api/jobs/<id>/interest/

    Un travailleur vérifié répond à une annonce ouverte. Cela crée (ou met à jour)
    sa mise en relation avec la famille, liée à cette annonce. La famille la voit
    dans /api/matches/ et peut accepter (match mutuel) ou refuser comme d'habitude.
    """

    permission_classes = [IsWorker]

    def post(self, request, pk):
        worker = getattr(request.user, "worker_profile", None)
        if worker is None:
            return Response({"detail": NO_WORKER_PROFILE}, status=status.HTTP_400_BAD_REQUEST)
        if not worker.is_verified:
            return Response({"detail": UNVERIFIED_WORKER_MESSAGE}, status=status.HTTP_403_FORBIDDEN)

        job = get_object_or_404(JobRequest.objects.open_to_workers(), pk=pk)
        match, created = Match.objects.get_or_create(client=job.client, worker=worker)
        match.job = job
        return interest_response(request, match, created)
