"""
Vues (endpoints) de l'app verification.
"""
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsWorker
from common.schema import AUTH_ERRORS, error, with_message

from .serializers import VerificationRecordSerializer, VerificationUploadSerializer

NO_PROFILE_MESSAGE = "Vous devez d'abord créer votre profil travailleur."


class VerificationDocumentsView(APIView):
    """
    GET  /api/verification/documents/ → voir ses documents et leur statut
    POST /api/verification/documents/ → envoyer un document
         (formulaire multipart : doc_type = "identite" ou "reference", file = le fichier)

    Réservé aux travailleurs ayant un profil.
    Le badge « vérifié » est accordé quand l'administrateur valide la pièce d'identité.
    """

    permission_classes = [IsWorker]

    def _get_worker(self, request):
        return getattr(request.user, "worker_profile", None)

    @extend_schema(
        tags=["Vérification"],
        summary="Mes documents et mon badge",
        responses={
            200: inline_serializer(
                name="MyVerification",
                fields={
                    "is_verified": drf_serializers.BooleanField(),
                    "documents": VerificationRecordSerializer(many=True),
                },
            ),
            404: error("Profil travailleur pas encore créé."),
            **AUTH_ERRORS,
        },
    )
    def get(self, request):
        worker = self._get_worker(request)
        if worker is None:
            return Response({"detail": NO_PROFILE_MESSAGE}, status=status.HTTP_404_NOT_FOUND)
        records = worker.verification_records.all()
        return Response(
            {
                "is_verified": worker.is_verified,
                "documents": VerificationRecordSerializer(records, many=True).data,
            }
        )

    @extend_schema(
        tags=["Vérification"],
        summary="Envoyer un document (pièce d'identité ou référence)",
        description="Formulaire multipart. Formats : PDF, JPG, PNG — 5 Mo maximum. "
        "Le badge « vérifié » est accordé quand l'équipe valide la pièce d'identité.",
        request={"multipart/form-data": VerificationUploadSerializer},
        responses={
            201: with_message("DocumentReceived", "document", VerificationRecordSerializer),
            400: error("Fichier invalide, trop lourd, ou document du même type déjà en attente/validé."),
            404: error("Profil travailleur pas encore créé."),
            **AUTH_ERRORS,
        },
    )
    def post(self, request):
        worker = self._get_worker(request)
        if worker is None:
            return Response({"detail": NO_PROFILE_MESSAGE}, status=status.HTTP_404_NOT_FOUND)
        serializer = VerificationUploadSerializer(data=request.data, context={"worker": worker})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            {
                "message": "Document reçu. Il sera examiné par l'équipe NOUNOU+.",
                "document": VerificationRecordSerializer(record).data,
            },
            status=status.HTTP_201_CREATED,
        )
