"""
Tests de l'app clients.
Couvre : création, consultation, modification du profil client, permissions.
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.services.models import Service
from common import choices


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    """Retourne un APIClient authentifié avec le token JWT de l'utilisateur."""
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def client_user(db):
    return User.objects.create_user(phone="+243822000001", role=User.ROLE_CLIENT)


@pytest.fixture
def worker_user(db):
    return User.objects.create_user(phone="+243822000002", role=User.ROLE_WORKER)


@pytest.fixture
def client_profile(client_user):
    profile = ClientProfile.objects.create(
        user=client_user,
        first_name="Jean",
        last_name="Ilunga",
        location="Golf",
        availability_needed=choices.AVAILABILITY_FULL,
        budget=Decimal("250.00"),
        needs_description="Deux enfants de 3 et 6 ans.",
    )
    profile.services_needed.set(Service.objects.filter(slug="nounou"))
    return profile


VALID_PAYLOAD = {
    "first_name": "Sarah",
    "last_name": "Kasongo",
    "location": "Bel-Air",
    "services_needed": "nounou,menage",
    "availability_needed": "temps_partiel",
    "budget": "150.00",
    "needs_description": "Aide pour les enfants l'après-midi.",
}


# ------------------------------------------------------------------ #
# Tests : création de profil                                           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestClientProfileCreate:
    url = reverse("clients-profile-create")

    def test_client_peut_creer_son_profil(self, client_user):
        response = auth_client(client_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        profile = response.data["profile"]
        assert profile["first_name"] == "Sarah"
        assert sorted(profile["services_list"]) == ["menage", "nounou"]
        assert ClientProfile.objects.filter(user=client_user).exists()

    def test_budget_facultatif(self, client_user):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "budget"}
        response = auth_client(client_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["profile"]["budget"] is None

    def test_travailleur_ne_peut_pas_creer_profil_client(self, worker_user):
        response = auth_client(worker_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self):
        response = APIClient().post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creation_doublon_interdit(self, client_user, client_profile):
        response = auth_client(client_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_service_invalide_rejete(self, client_user):
        payload = {**VALID_PAYLOAD, "services_needed": "chauffeur"}
        response = auth_client(client_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_budget_negatif_rejete(self, client_user):
        payload = {**VALID_PAYLOAD, "budget": "-10.00"}
        response = auth_client(client_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------------------------------------------ #
# Tests : consultation / modification de son propre profil            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestClientProfileMe:
    url = reverse("clients-profile-me")

    def test_client_peut_voir_son_profil(self, client_user, client_profile):
        response = auth_client(client_user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Jean"
        # Le client voit son propre nom complet
        assert response.data["last_name"] == "Ilunga"
        assert response.data["services_list"] == ["nounou"]

    def test_voir_profil_inexistant_retourne_404(self, client_user):
        response = auth_client(client_user).get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_client_peut_modifier_son_profil(self, client_user, client_profile):
        response = auth_client(client_user).patch(
            self.url, {"location": "Kenya", "services_needed": "cuisine"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["location"] == "Kenya"
        assert response.data["profile"]["services_list"] == ["cuisine"]

    def test_modification_partielle_ne_touche_pas_les_autres_champs(
        self, client_user, client_profile
    ):
        auth_client(client_user).patch(self.url, {"location": "Kamalondo"}, format="json")
        client_profile.refresh_from_db()
        assert client_profile.budget == Decimal("250.00")
        assert client_profile.get_services_list() == ["nounou"]

    def test_travailleur_ne_peut_pas_acceder_a_me(self, worker_user):
        response = auth_client(worker_user).get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
