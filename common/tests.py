"""
Tests de la documentation interactive de l'API.
"""
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestApiDocumentation:
    def test_page_swagger_accessible(self):
        response = APIClient().get(reverse("api-docs"))
        assert response.status_code == 200
        assert b"swagger" in response.content.lower()

    def test_page_redoc_accessible(self):
        assert APIClient().get(reverse("api-redoc")).status_code == 200

    def test_schema_openapi(self):
        response = APIClient().get(reverse("api-schema"), HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        assert response.json()["info"]["title"] == "API NOUNOU+"

    def test_fichiers_de_la_page_servis_localement(self):
        """La page ne dépend d'aucun site externe (utile avec une connexion lente)."""
        content = APIClient().get(reverse("api-docs")).content.decode()
        assert "cdn.jsdelivr.net" not in content
        assert "/static/drf_spectacular_sidecar/" in content

    def test_chaque_endpoint_est_documente_sans_avertissement(self, tmp_path):
        """Échoue si un nouvel endpoint est ajouté sans sa documentation."""
        call_command(
            "spectacular", "--file", str(tmp_path / "schema.yml"), "--validate", "--fail-on-warn"
        )
