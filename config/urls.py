"""
URLs centrales du projet — chaque app ajoute ses propres routes ici.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Renouvellement du token JWT (access expire en 12h, refresh en 7j)
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/workers/", include("apps.workers.urls")),
]
