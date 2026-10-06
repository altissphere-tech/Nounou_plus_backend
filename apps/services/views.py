"""
Vues (endpoints) de l'app services.
"""
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Service
from .serializers import ServiceSerializer


class ServiceListView(APIView):
    """
    GET /api/services/

    Liste des services proposés sur NOUNOU+ (nounou, ménage, cuisine…).
    Accessible sans connexion : utile pour remplir les formulaires de l'application.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Services"],
        summary="Liste des services",
        auth=[],
        responses=ServiceSerializer(many=True),
    )
    def get(self, request):
        return Response(ServiceSerializer(Service.objects.all(), many=True).data)
