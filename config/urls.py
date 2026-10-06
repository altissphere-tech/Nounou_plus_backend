"""
URLs centrales du projet — chaque app ajoute ses propres routes ici.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from apps.reviews.views import MatchReviewView

# Titres de l'interface d'administration
admin.site.site_header = "Administration NOUNOU+"
admin.site.site_title = "NOUNOU+ admin"
admin.site.index_title = "Tableau de bord"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Renouvellement du token JWT (access expire en 12h, refresh en 7j)
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
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
]
