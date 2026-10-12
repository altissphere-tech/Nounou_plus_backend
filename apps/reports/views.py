"""
Vues (endpoints) de l'app reports.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.workers.models import WorkerProfile
from common.pagination import paginated_response
from common.schema import AUTH_ERRORS, PAGINATION_PARAMETERS, error, paginated, with_message
from common.permissions import IsWorkerOrClient
from common.throttles import throttle

from .models import Report
from .serializers import ReportCreateSerializer, ReportSerializer


class ReportView(APIView):
    """
    POST /api/reports/ → signaler un profil
         { "profile_id": 12, "category": "arnaque", "description": "…" }
    GET  /api/reports/ → voir ses signalements (en attente / traité)

    Un client signale un profil travailleur (visible dans la liste ou dans ses matchs),
    un travailleur signale un profil client. Le signalement est anonyme.
    """

    permission_classes = [IsWorkerOrClient]
    throttle_classes = [throttle("reports")]

    @extend_schema(
        tags=["Signalements"],
        summary="Mes signalements (en attente / traité)",
        operation_id="reports_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: paginated("PaginatedReports", ReportSerializer), **AUTH_ERRORS},
    )
    def get(self, request):
        reports = request.user.reports_made.all()
        return paginated_response(request, self, reports, ReportSerializer)

    @extend_schema(
        tags=["Signalements"],
        summary="Signaler un profil (anonyme)",
        description="Client → `profile_id` d'un travailleur ; travailleur → `profile_id` d'un client. "
        "`description` est obligatoire pour la catégorie `autre`.",
        request=ReportCreateSerializer,
        responses={
            201: with_message("ReportCreated", "report", ReportSerializer),
            400: error("Données invalides, ou signalement déjà en cours pour ce profil."),
            404: error("Profil introuvable ou non visible."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile_id = serializer.validated_data["profile_id"]

        if request.user.role == User.ROLE_CLIENT:
            # Travailleurs visibles par ce client : vérifiés, ou déjà en relation avec lui
            visible = WorkerProfile.objects.active().filter(
                Q(is_verified=True) | Q(matches__client__user=request.user)
            )
            profile = get_object_or_404(visible.distinct(), pk=profile_id)
        else:
            # Familles visibles par ce travailleur : toutes s'il est vérifié, sinon celles
            # avec qui il est déjà en relation (on peut toujours signaler un abus subi)
            visible = ClientProfile.objects.active()
            worker = getattr(request.user, "worker_profile", None)
            if worker is None or not worker.is_verified:
                visible = visible.filter(matches__worker__user=request.user).distinct()
            profile = get_object_or_404(visible, pk=profile_id)

        if Report.objects.filter(
            reporter=request.user, target=profile.user, status=Report.STATUS_PENDING
        ).exists():
            return Response(
                {"detail": "Vous avez déjà un signalement en cours pour ce profil."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = Report.objects.create(
            reporter=request.user,
            target=profile.user,
            category=serializer.validated_data["category"],
            description=serializer.validated_data["description"],
        )
        return Response(
            {
                "message": (
                    "Merci, votre signalement a été transmis à l'équipe NOUNOU+. "
                    "La personne signalée ne saura pas que vous en êtes l'auteur."
                ),
                "report": ReportSerializer(report).data,
            },
            status=status.HTTP_201_CREATED,
        )
