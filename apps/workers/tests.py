"""
Tests de l'app workers.
Couvre : création, consultation, modification de profil, liste publique, permissions.
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.workers.models import WorkerProfile


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def get_token(user) -> str:
    """Retourne un token JWT access pour un utilisateur donné."""
    return str(RefreshToken.for_user(user).access_token)


def auth_client(user) -> APIClient:
    """Retourne un APIClient authentifié avec le token de l'utilisateur."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(user)}")
    return client


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def worker_user(db):
    return User.objects.create_user(phone="+243811000001", role=User.ROLE_WORKER)


@pytest.fixture
def worker_user_2(db):
    return User.objects.create_user(phone="+243811000002", role=User.ROLE_WORKER)


@pytest.fixture
def client_user(db):
    return User.objects.create_user(phone="+243811000003", role=User.ROLE_CLIENT)


@pytest.fixture
def worker_profile(worker_user):
    """Profil travailleur non vérifié."""
    return WorkerProfile.objects.create(
        user=worker_user,
        first_name="Marie",
        last_name="Kabila",
        services="nounou,cuisine",
        years_experience=3,
        availability=WorkerProfile.AVAILABILITY_FULL,
        expected_salary=Decimal("200.00"),
        location="Kampemba",
    )


@pytest.fixture
def verified_profile(worker_user_2):
    """Profil travailleur vérifié (visible dans la liste publique)."""
    return WorkerProfile.objects.create(
        user=worker_user_2,
        first_name="Grace",
        last_name="Mutombo",
        services="menage",
        years_experience=5,
        availability=WorkerProfile.AVAILABILITY_PART,
        expected_salary="150.00",
        location="Annexe",
        is_verified=True,
    )


VALID_PAYLOAD = {
    "first_name": "Alice",
    "last_name": "Ngoyi",
    "bio": "Expérimentée en garde d'enfants.",
    "services": "nounou",
    "years_experience": 2,
    "availability": "temps_plein",
    "expected_salary": "180.00",
    "location": "Lubumbashi Centre",
}


# ------------------------------------------------------------------ #
# Tests : création de profil                                           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestWorkerProfileCreate:
    url = reverse("workers-profile-create")

    def test_travailleur_peut_creer_son_profil(self, worker_user):
        response = auth_client(worker_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["profile"]["first_name"] == "Alice"
        assert WorkerProfile.objects.filter(user=worker_user).exists()

    def test_client_ne_peut_pas_creer_profil_travailleur(self, client_user):
        response = auth_client(client_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self):
        response = APIClient().post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_creation_doublon_interdit(self, worker_user, worker_profile):
        """Un travailleur ne peut pas créer deux profils."""
        response = auth_client(worker_user).post(self.url, VALID_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_service_invalide_rejete(self, worker_user):
        payload = {**VALID_PAYLOAD, "services": "chauffeur"}
        response = auth_client(worker_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_plusieurs_services_valides(self, worker_user):
        payload = {**VALID_PAYLOAD, "services": "nounou,cuisine"}
        response = auth_client(worker_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        services = response.data["profile"]["services_list"]
        assert "nounou" in services
        assert "cuisine" in services

    def test_is_verified_ne_peut_pas_etre_defini_a_linscription(self, worker_user):
        """Le champ is_verified est ignoré à la création — il reste False."""
        payload = {**VALID_PAYLOAD, "is_verified": True}
        response = auth_client(worker_user).post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["profile"]["is_verified"] is False


# ------------------------------------------------------------------ #
# Tests : consultation / modification de son propre profil            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestWorkerProfileMe:
    url = reverse("workers-profile-me")

    def test_travailleur_peut_voir_son_profil(self, worker_user, worker_profile):
        response = auth_client(worker_user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Marie"

    def test_voir_profil_inexistant_retourne_404(self, worker_user):
        response = auth_client(worker_user).get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_travailleur_peut_modifier_son_profil(self, worker_user, worker_profile):
        response = auth_client(worker_user).patch(
            self.url, {"location": "Kenya"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["location"] == "Kenya"
        worker_profile.refresh_from_db()
        assert worker_profile.location == "Kenya"

    def test_modification_partielle_ne_touche_pas_les_autres_champs(self, worker_user, worker_profile):
        original_salary = worker_profile.expected_salary
        auth_client(worker_user).patch(self.url, {"location": "Kamalondo"}, format="json")
        worker_profile.refresh_from_db()
        assert worker_profile.expected_salary == original_salary

    def test_travailleur_ne_peut_pas_se_verifier_lui_meme(self, worker_user, worker_profile):
        response = auth_client(worker_user).patch(
            self.url, {"is_verified": True}, format="json"
        )
        # La requête peut réussir (les autres champs sont modifiables)
        # mais is_verified reste False car le champ n'est pas dans le WriteSerializer
        worker_profile.refresh_from_db()
        assert worker_profile.is_verified is False

    def test_client_ne_peut_pas_acceder_a_me(self, client_user):
        response = auth_client(client_user).get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : liste publique des profils vérifiés                         #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestWorkerProfileList:
    url = reverse("workers-list")

    def test_liste_ne_retourne_que_les_verifies(
        self, client_user, worker_profile, verified_profile
    ):
        """worker_profile n'est pas vérifié → seul verified_profile doit apparaître."""
        response = auth_client(client_user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["first_name"] == "Grace"

    def test_travailleur_peut_voir_la_liste(self, worker_user, verified_profile):
        response = auth_client(worker_user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_liste_vide_si_aucun_verifie(self, client_user, worker_profile):
        response = auth_client(client_user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_telephone_masque_dans_la_liste(self, client_user, verified_profile):
        response = auth_client(client_user).get(self.url)
        phone_display = response.data["results"][0]["phone_display"]
        # Le numéro complet ne doit pas apparaître
        assert "+243811000002" not in phone_display
        assert "*" in phone_display

    def test_sans_token_retourne_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
