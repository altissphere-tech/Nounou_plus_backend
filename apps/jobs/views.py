"""
Vues (endpoints) de l'app jobs.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, PolymorphicProxySerializer, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.matching.models import Match
from apps.matching.views import INTEREST_RESPONSES, UNVERIFIED_WORKER_MESSAGE, interest_response
from common import choices
from common.filters import get_choice, get_decimal, get_text
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message
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

    @extend_schema(
        tags=["Annonces"],
        summary="Annonces ouvertes (travailleurs)",
        operation_id="jobs_list",
        parameters=[
            OpenApiParameter("service", str, description="Service demandé : nounou, menage ou cuisine."),
            OpenApiParameter("location", str, description="Quartier contenant ce texte."),
            OpenApiParameter(
                "availability", str, enum=[c[0] for c in choices.AVAILABILITY_CHOICES],
                description="Disponibilité requise.",
            ),
            OpenApiParameter("min_budget", float, description="Budget minimum."),
            *PAGINATION_PARAMETERS,
        ],
        responses={
            200: paginated("PaginatedJobs", JobRequestPublicSerializer),
            400: error("Valeur de filtre invalide."),
            **AUTH_ERRORS,
        },
    )
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

    @extend_schema(
        tags=["Annonces"],
        summary="Publier une annonce (clients)",
        request=JobRequestWriteSerializer,
        responses={
            201: with_message("JobCreated", "job", JobRequestSerializer),
            400: error("Données invalides, ou profil client pas encore créé."),
            **AUTH_ERRORS,
        },
    )
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

    @extend_schema(
        tags=["Annonces"],
        summary="Mes annonces (clients)",
        parameters=PAGINATION_PARAMETERS,
        responses={
            200: paginated("PaginatedMyJobs", JobRequestSerializer),
            404: error("Profil client pas encore créé."),
            **AUTH_ERRORS,
        },
    )
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

    @extend_schema(
        tags=["Annonces"],
        summary="Détail d'une annonce",
        description="Le client propriétaire voit son annonce (avec `interested_workers`) ; "
        "un travailleur voit une annonce ouverte (avec la famille présentée par prénom + initiale).",
        responses={
            200: PolymorphicProxySerializer(
                component_name="JobDetail",
                serializers=[JobRequestSerializer, JobRequestPublicSerializer],
                resource_type_field_name=None,
            ),
            404: error("Annonce introuvable, fermée, ou appartenant à une autre famille."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request, pk):
        if request.user.role == User.ROLE_CLIENT:
            job = get_object_or_404(JobRequest, pk=pk, client__user=request.user)
            return Response(JobRequestSerializer(job).data)
        job = get_object_or_404(JobRequest.objects.open_to_workers(), pk=pk)
        return Response(JobRequestPublicSerializer(job).data)

    @extend_schema(
        tags=["Annonces"],
        summary="Modifier mon annonce ou changer son statut (clients)",
        description="`status` : `ouverte`, `pourvue` ou `fermee` (les deux derniers la retirent "
        "de la liste des travailleurs).",
        request=JobRequestWriteSerializer,
        responses={
            200: with_message("JobUpdated", "job", JobRequestSerializer),
            400: error("Données invalides."),
            404: error("Annonce introuvable ou appartenant à une autre famille."),
            **AUTH_ERRORS,
        },
    )
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

    @extend_schema(
        tags=["Annonces"],
        summary="Répondre à une annonce (travailleurs vérifiés)",
        description="Crée (ou met à jour) la mise en relation avec la famille, liée à l'annonce.",
        request=None,
        responses={
            **INTEREST_RESPONSES,
            400: error("Profil travailleur pas encore créé."),
            401: AUTH_ERRORS[401],
            403: error("Rôle non autorisé, ou travailleur pas encore vérifié."),
            404: error("Annonce introuvable ou fermée."),
        },
    )
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
