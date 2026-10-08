"""
Tests de l'app matching.
Couvre : intérêt, match mutuel, refus discret, visibilité des coordonnées, permissions.
"""
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.matching.models import Match
from apps.services.models import Service
from apps.workers.models import WorkerProfile
from common import choices

CLIENT_PHONE = "+243833000001"
WORKER_PHONE = "+243833000002"


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def interest(user, profile_id):
    return auth_client(user).post(
        reverse("matches-interest"), {"profile_id": profile_id}, format="json"
    )


def decline(user, match_id):
    return auth_client(user).post(reverse("matches-decline", args=[match_id]))


def my_matches(user):
    return auth_client(user).get(reverse("matches-list")).data["results"]


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def client_profile(db):
    user = User.objects.create_user(phone=CLIENT_PHONE, role=User.ROLE_CLIENT, phone_verified=True)
    profile = ClientProfile.objects.create(
        user=user,
        first_name="Jean",
        last_name="Ilunga",
        location="Golf",
        availability_needed=choices.AVAILABILITY_FULL,
        budget=Decimal("250.00"),
    )
    profile.services_needed.set(Service.objects.filter(slug="nounou"))
    return profile


def _make_worker(phone, verified):
    user = User.objects.create_user(phone=phone, role=User.ROLE_WORKER, phone_verified=True)
    profile = WorkerProfile.objects.create(
        user=user,
        first_name="Grace",
        last_name="Mutombo",
        years_experience=5,
        availability=choices.AVAILABILITY_FULL,
        expected_salary=Decimal("200.00"),
        location="Annexe",
        is_verified=verified,
    )
    profile.services.set(Service.objects.filter(slug="nounou"))
    return profile


@pytest.fixture
def worker_profile(db):
    """Travailleur vérifié."""
    return _make_worker(WORKER_PHONE, verified=True)


@pytest.fixture
def unverified_worker(db):
    return _make_worker("+243833000003", verified=False)


@pytest.fixture
def mutual_match(client_profile, worker_profile):
    interest(client_profile.user, worker_profile.id)
    interest(worker_profile.user, client_profile.id)
    return Match.objects.get(client=client_profile, worker=worker_profile)


# ------------------------------------------------------------------ #
# Tests : manifester son intérêt                                      #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestInterest:
    def test_client_interesse_par_un_travailleur(self, client_profile, worker_profile):
        response = interest(client_profile.user, worker_profile.id)
        assert response.status_code == status.HTTP_201_CREATED
        match = response.data["match"]
        assert match["status"] == "en_attente"
        assert match["my_decision"] == "interesse"
        assert match["their_decision"] == "en_attente"

    def test_travailleur_voit_l_interet_recu(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        [match] = my_matches(worker_profile.user)
        assert match["my_decision"] == "en_attente"
        assert match["their_decision"] == "interesse"
        assert match["other_party"]["first_name"] == "Jean"

    def test_travailleur_interesse_par_un_client(self, client_profile, worker_profile):
        response = interest(worker_profile.user, client_profile.id)
        assert response.status_code == status.HTTP_201_CREATED
        assert Match.objects.filter(client=client_profile, worker=worker_profile).exists()

    def test_interet_en_double_ne_cree_pas_deux_matchs(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        response = interest(client_profile.user, worker_profile.id)
        assert response.status_code == status.HTTP_200_OK
        assert Match.objects.count() == 1

    def test_client_ne_peut_pas_cibler_un_travailleur_non_verifie(
        self, client_profile, unverified_worker
    ):
        response = interest(client_profile.user, unverified_worker.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_travailleur_non_verifie_ne_peut_pas_contacter(self, client_profile, unverified_worker):
        response = interest(unverified_worker.user, client_profile.id)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_profil_obligatoire(self, worker_profile):
        user = User.objects.create_user(phone="+243833000009", role=User.ROLE_CLIENT, phone_verified=True)
        response = interest(user, worker_profile.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_profil_inexistant_retourne_404(self, client_profile):
        response = interest(client_profile.user, 99999)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sans_token_retourne_401(self, worker_profile):
        response = APIClient().post(
            reverse("matches-interest"), {"profile_id": worker_profile.id}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : match mutuel et visibilité des coordonnées                  #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestMutualMatch:
    def test_coordonnees_masquees_avant_match(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        [match] = my_matches(client_profile.user)
        assert match["other_party"]["last_name"] == "M."
        assert match["other_party"]["phone"] is None
        assert WORKER_PHONE not in str(match)

    def test_match_devient_mutuel(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        response = interest(worker_profile.user, client_profile.id)
        assert response.data["match"]["status"] == "mutuel"
        assert response.data["match"]["mutual_at"] is not None

    def test_client_voit_coordonnees_completes_apres_match(self, mutual_match):
        [match] = my_matches(mutual_match.client.user)
        assert match["status"] == "mutuel"
        assert match["other_party"]["last_name"] == "Mutombo"
        assert match["other_party"]["phone"] == WORKER_PHONE

    def test_travailleur_voit_coordonnees_completes_apres_match(self, mutual_match):
        [match] = my_matches(mutual_match.worker.user)
        assert match["other_party"]["last_name"] == "Ilunga"
        assert match["other_party"]["phone"] == CLIENT_PHONE


# ------------------------------------------------------------------ #
# Tests : refus discret                                               #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestDecline:
    def test_refus_non_revele_a_l_autre(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        match = Match.objects.get()
        response = decline(worker_profile.user, match.id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["match"]["status"] == "refuse"

        # Le client ne voit pas le refus : sa demande reste « en attente »
        [seen_by_client] = my_matches(client_profile.user)
        assert seen_by_client["status"] == "en_attente"
        assert seen_by_client["their_decision"] == "en_attente"

    def test_refus_apres_match_masque_a_nouveau_les_coordonnees(self, mutual_match):
        decline(mutual_match.worker.user, mutual_match.id)
        [match] = my_matches(mutual_match.client.user)
        assert match["status"] == "en_attente"
        assert match["mutual_at"] is None
        assert match["other_party"]["phone"] is None
        assert match["other_party"]["last_name"] == "M."

    def test_revenir_sur_un_refus(self, mutual_match):
        decline(mutual_match.worker.user, mutual_match.id)
        response = interest(mutual_match.worker.user, mutual_match.client.id)
        assert response.data["match"]["status"] == "mutuel"

    def test_impossible_de_refuser_le_match_d_un_autre(self, mutual_match):
        stranger = _make_worker("+243833000007", verified=True)
        response = decline(stranger.user, mutual_match.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------------------------ #
# Tests : liste des matchs                                            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestMatchList:
    def test_chacun_ne_voit_que_ses_matchs(self, mutual_match):
        other_worker = _make_worker("+243833000008", verified=True)
        assert my_matches(other_worker.user) == []
        assert len(my_matches(mutual_match.client.user)) == 1

    def test_sans_token_retourne_401(self):
        response = APIClient().get(reverse("matches-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : un refus ne se devine pas, décisions simultanées             #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestDeclineStaysHidden:
    def test_refus_ne_change_ni_la_date_ni_l_ordre(self, client_profile, worker_profile, unverified_worker):
        """Faille M1 : après un refus de l'autre, rien ne bouge pour celui qui a demandé."""
        unverified_worker.is_verified = True
        unverified_worker.save()
        interest(client_profile.user, worker_profile.id)
        interest(client_profile.user, unverified_worker.id)  # plus récent : en tête de liste
        before = my_matches(client_profile.user)
        match = Match.objects.get(worker=worker_profile)
        decline(worker_profile.user, match.id)
        after = my_matches(client_profile.user)
        assert [m["id"] for m in after] == [m["id"] for m in before]
        assert after == before

    def test_interet_de_l_autre_fait_remonter(self, client_profile, worker_profile, unverified_worker):
        unverified_worker.is_verified = True
        unverified_worker.save()
        interest(client_profile.user, worker_profile.id)
        interest(client_profile.user, unverified_worker.id)
        interest(worker_profile.user, client_profile.id)  # match mutuel : visible, donc remonte
        assert my_matches(client_profile.user)[0]["other_party"]["id"] == worker_profile.id

    def test_decision_simultanee_n_ecrase_pas_un_refus(self, client_profile, worker_profile):
        """Faille M2 : une copie périmée du match ne peut pas effacer le refus de l'autre."""
        interest(worker_profile.user, client_profile.id)
        stale = Match.objects.get()  # lue par la famille avant le refus
        decline(worker_profile.user, stale.id)  # la nounou refuse au même moment
        stale.set_decision(client_profile.user, Match.DECISION_INTERESTED)
        match = Match.objects.get()
        assert match.worker_decision == Match.DECISION_DECLINED
        assert not match.is_mutual and match.mutual_at is None
        assert my_matches(client_profile.user)[0]["other_party"]["phone"] is None


@pytest.mark.django_db
def test_numero_non_confirme_invisible(client_profile, worker_profile):
    """Faille E3 : un compte dont le numéro n'est pas confirmé n'apparaît nulle part."""
    User.objects.filter(pk=worker_profile.user_id).update(phone_verified=False)
    assert interest(client_profile.user, worker_profile.id).status_code == status.HTTP_404_NOT_FOUND
    assert auth_client(client_profile.user).get(reverse("workers-list")).data["count"] == 0
