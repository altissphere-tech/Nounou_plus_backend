"""
Tests de l'app accounts.

Chaque test vérifie un scénario critique : inscription, OTP, connexion, profil.
On utilise pytest + pytest-django (plus simple et plus rapide que le TestCase de Django).
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User


# ------------------------------------------------------------------ #
# Fixtures — données réutilisables dans tous les tests               #
# ------------------------------------------------------------------ #

@pytest.fixture
def api_client():
    """Client HTTP pour simuler des appels à l'API."""
    return APIClient()


@pytest.fixture
def registered_user(db):
    """Crée un utilisateur en base et génère son OTP."""
    user = User.objects.create_user(phone="+243812345678", role=User.ROLE_CLIENT)
    user.generate_otp()
    return user


@pytest.fixture
def authenticated_client(api_client, registered_user):
    """Client HTTP avec un token JWT valide (utilisateur déjà connecté)."""
    # On vérifie l'OTP pour obtenir un token
    response = api_client.post(
        reverse("accounts-otp-verify"),
        {"phone": "+243812345678", "code": "123456"},
        format="json",
    )
    token = response.data["tokens"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ------------------------------------------------------------------ #
# Tests d'inscription                                                  #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestRegister:
    def test_inscription_client_reussie(self, api_client):
        """Un client peut créer un compte avec un numéro valide."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812345678", "role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == "client"
        assert User.objects.filter(phone="+243812345678").exists()

    def test_inscription_travailleur_reussie(self, api_client):
        """Un travailleur peut créer un compte avec un numéro valide."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243897654321", "role": "travailleur"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == "travailleur"

    def test_inscription_doublon_interdit(self, api_client, registered_user):
        """On ne peut pas créer deux comptes avec le même numéro."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812345678", "role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inscription_role_admin_interdit(self, api_client):
        """Le rôle 'admin' ne peut pas être choisi lors de l'inscription via l'API."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243811111111", "role": "admin"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inscription_sans_telephone_echoue(self, api_client):
        """L'inscription échoue si le numéro de téléphone est absent."""
        response = api_client.post(
            reverse("accounts-register"),
            {"role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------------------------------------------ #
# Tests OTP                                                            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestOTP:
    def test_demande_otp_valide(self, api_client, registered_user):
        """La demande d'OTP réussit pour un numéro existant."""
        response = api_client.post(
            reverse("accounts-otp-request"),
            {"phone": "+243812345678"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_demande_otp_numero_inconnu(self, api_client):
        """La demande d'OTP échoue si le numéro n'est pas enregistré."""
        response = api_client.post(
            reverse("accounts-otp-request"),
            {"phone": "+243899999999"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verification_otp_correcte(self, api_client, registered_user):
        """Un code OTP correct retourne des tokens JWT."""
        response = api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "123456"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_verification_otp_incorrecte(self, api_client, registered_user):
        """Un code OTP incorrect est refusé."""
        response = api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "000000"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_telephone_marque_verifie_apres_otp(self, api_client, registered_user):
        """Après vérification OTP réussie, phone_verified passe à True."""
        api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "123456"},
            format="json",
        )
        registered_user.refresh_from_db()
        assert registered_user.phone_verified is True


# ------------------------------------------------------------------ #
# Tests profil /me/                                                    #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestMe:
    def test_profil_accessible_avec_token(self, authenticated_client):
        """Un utilisateur connecté peut accéder à son profil."""
        response = authenticated_client.get(reverse("accounts-me"))
        assert response.status_code == status.HTTP_200_OK
        assert "phone" in response.data
        assert "role" in response.data

    def test_profil_inaccessible_sans_token(self, api_client):
        """Sans token JWT, /me/ retourne 401."""
        response = api_client.get(reverse("accounts-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
