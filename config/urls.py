"""
URLs centrales du projet — chaque app ajoute ses propres routes ici.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import PublicPhotoView
from apps.reviews.views import MatchReviewView

# Titres de l'interface d'administration
admin.site.site_header = "Administration NOUNOU+"
admin.site.site_title = "NOUNOU+ admin"
admin.site.index_title = "Tableau de bord"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # Documentation interactive de l'API
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    # Renouvellement du token JWT (access : 10 min ; refresh : 30 min d'inactivité)
    path(
        "api/token/refresh/",
        extend_schema_view(
            post=extend_schema(
                tags=["Comptes"],
                summary="Renouveler le token d'accès (avec le token refresh)",
                description="Le token `access` expire après 10 min. Envoyez le `refresh` "
                "pour en obtenir un nouveau, sans redemander de code SMS. Un refresh ne sert "
                "qu'une fois (la réponse en contient un nouveau) et expire après 30 min "
                "d'inactivité.",
                auth=[],
            )
        )(TokenRefreshView).as_view(),
        name="token-refresh",
    ),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/workers/", include("apps.workers.urls")),
    path("api/clients/", include("apps.clients.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/services/", include("apps.services.urls")),
    path("api/matches/", include("apps.matching.urls")),
    path("api/matches/<int:match_id>/messages/", include("apps.messaging.urls")),
    path("api/verification/", include("apps.verification.urls")),
    path("api/matches/<int:match_id>/review/", MatchReviewView.as_view(), name="matches-review"),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/favorites/", include("apps.favorites.urls")),
    path("api/photos/<str:name>", PublicPhotoView.as_view(), name="public-photo"),
]
