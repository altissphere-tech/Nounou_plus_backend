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
from apps.services.models import Service
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
    return User.objects.create_user(phone="+243811000001", role=User.ROLE_WORKER, phone_verified=True)


@pytest.fixture
def worker_user_2(db):
    return User.objects.create_user(phone="+243811000002", role=User.ROLE_WORKER, phone_verified=True)


@pytest.fixture
def client_user(db):
    return User.objects.create_user(phone="+243811000003", role=User.ROLE_CLIENT, phone_verified=True)


@pytest.fixture
def worker_profile(worker_user):
    """Profil travailleur non vérifié."""
    profile = WorkerProfile.objects.create(
        user=worker_user,
        first_name="Marie",
        last_name="Kabila",
        years_experience=3,
        availability=WorkerProfile.AVAILABILITY_FULL,
        expected_salary=Decimal("200.00"),
        location="Kampemba",
    )
    profile.services.set(Service.objects.filter(slug__in=["nounou", "cuisine"]))
    return profile


@pytest.fixture
def verified_profile(worker_user_2):
    """Profil travailleur vérifié (visible dans la liste publique)."""
    profile = WorkerProfile.objects.create(
        user=worker_user_2,
        first_name="Grace",
        last_name="Mutombo",
        years_experience=5,
        availability=WorkerProfile.AVAILABILITY_PART,
        expected_salary="150.00",
        location="Annexe",
        is_verified=True,
    )
    profile.services.set(Service.objects.filter(slug="menage"))
    return profile


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
        # Le travailleur voit son propre nom complet
        assert response.data["last_name"] == "Kabila"

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

    def test_nom_de_famille_masque_dans_la_liste(self, client_user, verified_profile):
        result = auth_client(client_user).get(self.url).data["results"][0]
        assert result["first_name"] == "Grace"
        assert result["last_name"] == "M."

    def test_telephone_masque_dans_la_liste(self, client_user, verified_profile):
        response = auth_client(client_user).get(self.url)
        phone_display = response.data["results"][0]["phone_display"]
        # Le numéro complet ne doit pas apparaître
        assert "+243811000002" not in phone_display
        assert "*" in phone_display

    def test_sans_token_retourne_401(self):
        response = APIClient().get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : recherche avec filtres, tri et pagination                   #
# ------------------------------------------------------------------ #

def _verified_worker(n, services, salary, experience, location, availability):
    user = User.objects.create_user(phone=f"+24381200{n:04d}", role=User.ROLE_WORKER, phone_verified=True)
    profile = WorkerProfile.objects.create(
        user=user,
        first_name=f"Travailleur{n}",
        last_name="Test",
        years_experience=experience,
        availability=availability,
        expected_salary=Decimal(salary),
        location=location,
        is_verified=True,
    )
    profile.services.set(Service.objects.filter(slug__in=services))
    return profile


@pytest.mark.django_db
class TestWorkerSearch:
    url = reverse("workers-list")

    @pytest.fixture
    def workers(self, db):
        return {
            "nounou_kenya": _verified_worker(1, ["nounou"], "150", 2, "Kenya", "temps_plein"),
            "cuisine_golf": _verified_worker(2, ["cuisine", "menage"], "300", 8, "Golf", "temps_partiel"),
            "menage_kenya": _verified_worker(3, ["menage"], "100", 0, "Kenya", "weekends"),
        }

    def _names(self, client_user, **params):
        response = auth_client(client_user).get(self.url, params)
        assert response.status_code == status.HTTP_200_OK, response.data
        return {r["first_name"] for r in response.data["results"]}

    def test_sans_filtre(self, client_user, workers):
        assert len(self._names(client_user)) == 3

    def test_filtre_service(self, client_user, workers):
        assert self._names(client_user, service="menage") == {"Travailleur2", "Travailleur3"}

    def test_filtre_quartier_insensible_a_la_casse(self, client_user, workers):
        assert self._names(client_user, location="kenya") == {"Travailleur1", "Travailleur3"}

    def test_filtre_disponibilite(self, client_user, workers):
        assert self._names(client_user, availability="weekends") == {"Travailleur3"}

    def test_filtre_salaire_maximum(self, client_user, workers):
        assert self._names(client_user, max_salary="150") == {"Travailleur1", "Travailleur3"}

    def test_filtre_experience_minimum(self, client_user, workers):
        assert self._names(client_user, min_experience="2") == {"Travailleur1", "Travailleur2"}

    def test_filtres_combines(self, client_user, workers):
        assert self._names(client_user, location="kenya", service="nounou") == {"Travailleur1"}

    def test_tri_par_salaire(self, client_user, workers):
        response = auth_client(client_user).get(self.url, {"ordering": "salary"})
        salaries = [r["expected_salary"] for r in response.data["results"]]
        assert salaries == ["100.00", "150.00", "300.00"]

    def test_tri_par_experience(self, client_user, workers):
        response = auth_client(client_user).get(self.url, {"ordering": "experience"})
        assert [r["years_experience"] for r in response.data["results"]] == [8, 2, 0]

    def test_tri_par_note(self, client_user, workers):
        response = auth_client(client_user).get(self.url, {"ordering": "rating"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_valeur_invalide_renvoie_400(self, client_user, workers):
        # « NaN » / « Infinity » : erreur 400, jamais une erreur du serveur (test d'intrusion 2026)
        for params in ({"max_salary": "beaucoup"}, {"min_experience": "-1"},
                       {"availability": "nuit"}, {"ordering": "nom"},
                       {"max_salary": "NaN"}, {"max_salary": "sNaN"}, {"max_salary": "Infinity"}):
            response = auth_client(client_user).get(self.url, params)
            assert response.status_code == status.HTTP_400_BAD_REQUEST, params

    def test_pagination(self, client_user, workers):
        response = auth_client(client_user).get(self.url, {"page_size": 2})
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 2
        assert response.data["next"] is not None
        response = auth_client(client_user).get(self.url, {"page_size": 2, "page": 2})
        assert len(response.data["results"]) == 1
        assert response.data["next"] is None

    def test_page_inexistante_renvoie_404(self, client_user, workers):
        response = auth_client(client_user).get(self.url, {"page": 99})
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------ #
# Tests : fiche d'un travailleur                                      #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestWorkerProfileDetail:
    def test_client_voit_la_fiche_d_un_travailleur_verifie(self, client_user, verified_profile):
        url = reverse("workers-detail", args=[verified_profile.id])
        response = auth_client(client_user).get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Grace"
        # Mêmes règles de confidentialité que la liste
        assert response.data["last_name"] == "M."
        assert "+243811000002" not in str(response.data)

    def test_profil_non_verifie_introuvable(self, client_user, worker_profile):
        url = reverse("workers-detail", args=[worker_profile.id])
        assert auth_client(client_user).get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_compte_suspendu_introuvable(self, client_user, verified_profile):
        User.objects.filter(pk=verified_profile.user_id).update(is_active=False)
        url = reverse("workers-detail", args=[verified_profile.id])
        assert auth_client(client_user).get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_sans_token_retourne_401(self, verified_profile):
        url = reverse("workers-detail", args=[verified_profile.id])
        assert APIClient().get(url).status_code == status.HTTP_401_UNAUTHORIZED
