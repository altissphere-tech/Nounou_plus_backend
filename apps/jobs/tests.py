"""
Tests de l'app jobs.
Couvre : publication, plusieurs annonces par famille, consultation et filtres
par les travailleurs, confidentialité, statuts, réponse à une annonce (match).
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.jobs.models import JobRequest
from apps.matching.models import Match
from apps.services.models import Service
from apps.workers.models import WorkerProfile
from common import choices

CLIENT_PHONE = "+243814400001"

NOUNOU_JOB = {
    "title": "Nounou pour 2 enfants",
    "service": "nounou",
    "availability": "temps_plein",
    "budget": "200",
    "description": "Du lundi au vendredi, 7h-17h.",
}
CUISINE_JOB = {
    "title": "Cuisinière le week-end",
    "service": "cuisine",
    "availability": "weekends",
    "location": "Bel-Air",
}


# ------------------------------------------------------------------ #
# Helpers & fixtures                                                   #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def publish(user, data):
    return auth_client(user).post(reverse("jobs-list"), data, format="json")


def make_worker(phone, verified=True):
    user = User.objects.create_user(phone=phone, role=User.ROLE_WORKER, phone_verified=True)
    return WorkerProfile.objects.create(
        user=user, first_name="Grace", last_name="Mutombo",
        availability=choices.AVAILABILITY_FULL, expected_salary=Decimal("200.00"),
        location="Annexe", is_verified=verified,
    )


@pytest.fixture
def client_profile(db):
    user = User.objects.create_user(phone=CLIENT_PHONE, role=User.ROLE_CLIENT, phone_verified=True)
    return ClientProfile.objects.create(
        user=user, first_name="Sarah", last_name="Kasongo",
        location="Golf", availability_needed=choices.AVAILABILITY_FULL,
    )


@pytest.fixture
def worker(db):
    return make_worker("+243814400002")


@pytest.fixture
def jobs(client_profile):
    """Deux annonces de la même famille."""
    publish(client_profile.user, NOUNOU_JOB)
    publish(client_profile.user, CUISINE_JOB)
    return {job.service.slug: job for job in JobRequest.objects.all()}


# ------------------------------------------------------------------ #
# Tests : publier et gérer ses annonces (famille)                     #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestPublish:
    def test_famille_publie_une_annonce(self, client_profile):
        response = publish(client_profile.user, NOUNOU_JOB)
        assert response.status_code == status.HTTP_201_CREATED
        job = response.data["job"]
        assert job["status"] == "ouverte"
        assert job["service"]["slug"] == "nounou"
        # Quartier repris du profil quand il n'est pas précisé
        assert job["location"] == "Golf"

    def test_plusieurs_annonces_par_famille(self, client_profile, jobs):
        response = auth_client(client_profile.user).get(reverse("jobs-mine"))
        assert response.data["count"] == 2
        assert {j["service"]["slug"] for j in response.data["results"]} == {"nounou", "cuisine"}

    def test_service_invalide(self, client_profile):
        response = publish(client_profile.user, {**NOUNOU_JOB, "service": "chauffeur"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nouvelle_annonce_toujours_ouverte(self, client_profile):
        response = publish(client_profile.user, {**NOUNOU_JOB, "status": "pourvue"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_profil_client_obligatoire(self, db):
        user = User.objects.create_user(phone="+243814400009", role=User.ROLE_CLIENT, phone_verified=True)
        assert publish(user, NOUNOU_JOB).status_code == status.HTTP_400_BAD_REQUEST

    def test_travailleur_ne_peut_pas_publier(self, worker):
        assert publish(worker.user, NOUNOU_JOB).status_code == status.HTTP_403_FORBIDDEN

    def test_modifier_son_annonce(self, client_profile, jobs):
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        response = auth_client(client_profile.user).patch(url, {"budget": "250"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["job"]["budget"] == "250.00"

    def test_marquer_pourvue(self, client_profile, jobs):
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        auth_client(client_profile.user).patch(url, {"status": "pourvue"}, format="json")
        jobs["nounou"].refresh_from_db()
        assert jobs["nounou"].status == "pourvue"

    def test_impossible_de_modifier_l_annonce_d_une_autre_famille(self, jobs):
        other = User.objects.create_user(phone="+243814400008", role=User.ROLE_CLIENT, phone_verified=True)
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        response = auth_client(other).patch(url, {"budget": "1"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_travailleur_ne_peut_pas_modifier(self, worker, jobs):
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        response = auth_client(worker.user).patch(url, {"budget": "1"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ------------------------------------------------------------------ #
# Tests : consultation par les travailleurs                           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestBrowse:
    def test_travailleur_voit_les_annonces_ouvertes(self, worker, jobs):
        response = auth_client(worker.user).get(reverse("jobs-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_famille_presentee_sans_nom_complet_ni_telephone(self, worker, jobs):
        data = auth_client(worker.user).get(reverse("jobs-list")).data
        assert data["results"][0]["client"]["name"] == "Sarah K."
        assert "Kasongo" not in str(data)
        assert CLIENT_PHONE not in str(data)

    def test_filtres(self, worker, jobs):
        api = auth_client(worker.user)
        url = reverse("jobs-list")
        assert api.get(url, {"service": "cuisine"}).data["count"] == 1
        assert api.get(url, {"location": "bel-air"}).data["count"] == 1
        assert api.get(url, {"availability": "temps_plein"}).data["count"] == 1
        # L'annonce cuisine n'a pas de budget : exclue du filtre budget
        assert api.get(url, {"min_budget": "100"}).data["count"] == 1

    def test_travailleur_non_verifie_ne_voit_ni_familles_ni_annonces(self, jobs):
        """Faille M3 : un compte travailleur non vérifié ne peut pas parcourir les familles."""
        unverified = make_worker("+243814400077", verified=False)
        api = auth_client(unverified.user)
        assert api.get(reverse("jobs-list")).status_code == status.HTTP_403_FORBIDDEN
        detail = api.get(reverse("jobs-detail", args=[jobs["nounou"].id]))
        assert detail.status_code == status.HTTP_403_FORBIDDEN and "Sarah" not in str(detail.data)
        assert api.get(reverse("clients-list")).status_code == status.HTTP_403_FORBIDDEN
        assert api.put(reverse("favorites-job", args=[jobs["nounou"].id])).status_code == status.HTTP_403_FORBIDDEN

    def test_annonce_pourvue_retiree_de_la_liste(self, worker, jobs):
        JobRequest.objects.filter(pk=jobs["nounou"].pk).update(status=JobRequest.STATUS_FILLED)
        assert auth_client(worker.user).get(reverse("jobs-list")).data["count"] == 1
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        assert auth_client(worker.user).get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_annonces_d_un_compte_suspendu_retirees(self, worker, jobs, client_profile):
        User.objects.filter(pk=client_profile.user.pk).update(is_active=False)
        assert auth_client(worker.user).get(reverse("jobs-list")).data["count"] == 0

    def test_client_ne_voit_pas_la_liste_publique(self, client_profile, jobs):
        response = auth_client(client_profile.user).get(reverse("jobs-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ------------------------------------------------------------------ #
# Tests : répondre à une annonce                                      #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestApply:
    def test_travailleur_repond_a_une_annonce(self, worker, jobs):
        url = reverse("jobs-interest", args=[jobs["nounou"].id])
        response = auth_client(worker.user).post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["match"]["job"] == {"id": jobs["nounou"].id, "title": "Nounou pour 2 enfants"}
        match = Match.objects.get()
        assert match.job == jobs["nounou"]
        assert match.worker_decision == Match.DECISION_INTERESTED

    def test_famille_voit_la_reponse_et_accepte(self, worker, jobs, client_profile):
        auth_client(worker.user).post(reverse("jobs-interest", args=[jobs["nounou"].id]))
        api = auth_client(client_profile.user)
        [match] = api.get(reverse("matches-list")).data["results"]
        assert match["job"]["title"] == "Nounou pour 2 enfants"
        assert match["their_decision"] == "interesse"
        response = api.post(reverse("matches-interest"), {"profile_id": worker.id}, format="json")
        assert response.data["match"]["status"] == "mutuel"

    def test_compteur_de_reponses_pour_la_famille(self, worker, jobs, client_profile):
        auth_client(worker.user).post(reverse("jobs-interest", args=[jobs["nounou"].id]))
        url = reverse("jobs-detail", args=[jobs["nounou"].id])
        assert auth_client(client_profile.user).get(url).data["interested_workers"] == 1

    def test_travailleur_non_verifie_refuse(self, jobs):
        unverified = make_worker("+243814400003", verified=False)
        url = reverse("jobs-interest", args=[jobs["nounou"].id])
        assert auth_client(unverified.user).post(url).status_code == status.HTTP_403_FORBIDDEN

    def test_annonce_fermee_refusee(self, worker, jobs):
        JobRequest.objects.filter(pk=jobs["nounou"].pk).update(status=JobRequest.STATUS_CLOSED)
        url = reverse("jobs-interest", args=[jobs["nounou"].id])
        assert auth_client(worker.user).post(url).status_code == status.HTTP_404_NOT_FOUND

    def test_client_ne_peut_pas_repondre(self, client_profile, jobs):
        url = reverse("jobs-interest", args=[jobs["nounou"].id])
        assert auth_client(client_profile.user).post(url).status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self, jobs):
        assert APIClient().get(reverse("jobs-list")).status_code == status.HTTP_401_UNAUTHORIZED
