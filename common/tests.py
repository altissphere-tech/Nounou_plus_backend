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


# ------------------------------------------------------------------ #
# Limites d'essais (anti-abus)                                         #
# ------------------------------------------------------------------ #

import pytest  # noqa: E402
from django.urls import reverse  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402
from rest_framework.throttling import SimpleRateThrottle  # noqa: E402

from apps.accounts.models import User  # noqa: E402


@pytest.fixture
def rates(monkeypatch):
    """Active de petites limites pour le test (les tests normaux n'en ont pas)."""

    def set_rates(**values):
        monkeypatch.setattr(SimpleRateThrottle, "THROTTLE_RATES", {**SimpleRateThrottle.THROTTLE_RATES, **values})

    return set_rates


def post(client, name, data, **extra):
    return client.post(reverse(name), data, format="json", **extra).status_code


@pytest.mark.django_db
class TestThrottles:
    def test_x_forwarded_for_ne_contourne_pas_la_limite(self, rates):
        rates(auth="3/min")
        client = APIClient()
        codes = [
            post(client, "accounts-login", {"email": "a@b.cd", "password": "x"}, HTTP_X_FORWARDED_FOR=f"10.0.0.{i}")
            for i in range(5)
        ]
        assert codes[-1] == 429

    def test_codes_sms_limites_par_numero_meme_depuis_plusieurs_appareils(self, rates):
        rates(sms_phone="3/hour")
        User.objects.create_user(phone="+243812300001", role="client")
        codes = [
            post(APIClient(REMOTE_ADDR=f"10.0.0.{i}"), "accounts-otp-request", {"phone": "0812300001" if i % 2 else "+243812300001"})
            for i in range(5)
        ]
        assert codes[:3] == [200, 200, 200]
        assert codes[3] == 429  # « 081… » et « +243 81… » comptent pour le même numéro

    def test_essais_de_code_limites(self, rates):
        rates(otp_verify_phone="5/hour")
        User.objects.create_user(phone="+243812300001", role="client").generate_otp()
        client = APIClient()
        codes = [post(client, "accounts-otp-verify", {"phone": "+243812300001", "code": f"{i:06d}"}) for i in range(7)]
        assert 429 in codes
        # Même le bon code est refusé tant que la limite est atteinte
        assert post(client, "accounts-otp-verify", {"phone": "+243812300001", "code": "123456"}) == 429

    def test_inscriptions_limitees(self, rates):
        rates(register="3/hour")
        client = APIClient()
        codes = [post(client, "accounts-register", {"phone": f"+24381230{i:04d}", "role": "client"}) for i in range(5)]
        assert codes[:3] == [201, 201, 201] and codes[3] == 429

    def test_connexion_limitee_par_email(self, rates):
        rates(login_email="3/hour")
        codes = [
            post(APIClient(REMOTE_ADDR=f"10.0.1.{i}"), "accounts-login", {"email": "Cible@Example.com", "password": "x"})
            for i in range(5)
        ]
        assert codes[3] == 429

    def test_lecture_jamais_limitee(self, rates):
        from rest_framework_simplejwt.tokens import RefreshToken

        rates(messages="1/min")
        user = User.objects.create_user(phone="+243812300001", role="client")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
        # GET d'une conversation inexistante : 404, jamais 429
        assert {client.get(reverse("messages-conversation", args=[999])).status_code for _ in range(5)} == {404}


# ------------------------------------------------------------------ #
# En-têtes de sécurité et journal                                      #
# ------------------------------------------------------------------ #


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_reponses_api(self):
        response = APIClient().get("/api/services/")
        assert response["Content-Security-Policy"].startswith("default-src 'none'")
        assert response["Cache-Control"] == "no-store"  # données jamais gardées en cache
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["X-Frame-Options"] == "DENY"
        assert "camera=()" in response["Permissions-Policy"]

    def test_photos_publiques_peuvent_etre_mises_en_cache(self):
        response = APIClient().get("/api/photos/inconnue.jpg")
        assert response.status_code == 404
        assert response.get("Cache-Control") != "no-store"


@pytest.fixture
def security_log(caplog):
    """Le journal de sécurité ne remonte pas au journal général : on l'écoute directement."""
    import logging

    logger = logging.getLogger("nounou.security")
    logger.addHandler(caplog.handler)
    caplog.set_level("INFO", logger="nounou.security")
    yield caplog
    logger.removeHandler(caplog.handler)


@pytest.mark.django_db
class TestSecurityLog:
    def test_echec_de_connexion_note_sans_donnee_personnelle(self, security_log):
        caplog = security_log
        APIClient().post(reverse("accounts-login"), {"email": "marie@example.com", "password": "Secret123!"}, format="json")
        line = caplog.text
        assert "connexion_refusee" in line
        assert "marie" not in line and "Secret123" not in line

    def test_limite_atteinte_notee(self, security_log, rates):
        caplog = security_log
        rates(auth="1/min")
        client = APIClient()
        for _ in range(2):
            client.post(reverse("accounts-login"), {"email": "a@b.cd", "password": "x"}, format="json")
        assert "limite_atteinte" in caplog.text and "EmailLoginView" in caplog.text

    def test_une_valeur_ne_peut_pas_creer_une_fausse_ligne(self, security_log):
        from common.security_log import event

        event("essai", chemin="/api/x\nconnexion ip=1.2.3.4 compte=1")
        assert "\nconnexion" not in security_log.text
        assert "\\nconnexion" in security_log.text


def test_serveur_refuse_de_demarrer_sans_reglages(tmp_path):
    """Faille E1 : sans DJANGO_SETTINGS_MODULE, le serveur ne démarre pas en mode développement."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent
    # Copie de wsgi.py hors du projet : aucun fichier .env ne peut fournir le réglage
    (tmp_path / "wsgi_copy.py").write_text((repo / "config" / "wsgi.py").read_text())
    env = {key: value for key, value in os.environ.items() if key != "DJANGO_SETTINGS_MODULE"}
    env["PYTHONPATH"] = str(repo)
    result = subprocess.run(
        [sys.executable, "-c", "import wsgi_copy"], cwd=tmp_path, env=env, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "DJANGO_SETTINGS_MODULE manquant" in result.stderr
