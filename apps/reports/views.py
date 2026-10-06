"""
Vues (endpoints) de l'app reports.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.workers.models import WorkerProfile
from common.permissions import IsWorkerOrClient

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

    def get(self, request):
        reports = request.user.reports_made.all()
        return Response({"results": ReportSerializer(reports, many=True).data})

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
            profile = get_object_or_404(ClientProfile.objects.active(), pk=profile_id)

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
