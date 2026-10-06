"""
Tests de l'app reviews.
Couvre : délai d'essai, une seule évaluation par personne, critères selon le rôle,
moyennes sur le profil, affichage public, modération, permissions.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.clients.models import ClientProfile
from apps.matching.models import Match
from apps.reviews.models import Review
from apps.workers.models import WorkerProfile
from common import choices

WORKER_SCORES = {"punctuality": 5, "competence": 4, "reliability": 4}
CLIENT_SCORES = {"respect": 5, "clarity": 3, "payment_on_time": 4}


# ------------------------------------------------------------------ #
# Helpers & fixtures                                                   #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def review(user, match, data):
    return auth_client(user).post(reverse("matches-review", args=[match.id]), data, format="json")


def make_match(n, days_ago=8):
    """Crée un match mutuel dont le premier match date de `days_ago` jours."""
    client_user = User.objects.create_user(phone=f"+24386600{n}1", role=User.ROLE_CLIENT)
    worker_user = User.objects.create_user(phone=f"+24386600{n}2", role=User.ROLE_WORKER)
    client = ClientProfile.objects.create(
        user=client_user, first_name="Jean", last_name="Ilunga",
        location="Golf", availability_needed=choices.AVAILABILITY_FULL,
    )
    worker = WorkerProfile.objects.create(
        user=worker_user, first_name="Grace", last_name="Mutombo",
        availability=choices.AVAILABILITY_FULL, expected_salary=Decimal("200.00"),
        location="Annexe", is_verified=True,
    )
    match = Match.objects.create(client=client, worker=worker)
    match.set_decision(client_user, Match.DECISION_INTERESTED)
    match.set_decision(worker_user, Match.DECISION_INTERESTED)
    Match.objects.filter(pk=match.pk).update(
        first_mutual_at=timezone.now() - timedelta(days=days_ago)
    )
    match.refresh_from_db()
    return match


@pytest.fixture
def match(db):
    """Match mutuel dont la période d'essai (7 jours) est écoulée."""
    return make_match(1)


@pytest.fixture
def recent_match(db):
    """Match mutuel d'il y a 2 jours : trop tôt pour évaluer."""
    return make_match(2, days_ago=2)


# ------------------------------------------------------------------ #
# Tests : laisser une évaluation                                      #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestCreateReview:
    def test_client_evalue_le_travailleur(self, match):
        response = review(match.client.user, match, {**WORKER_SCORES, "comment": "Très sérieuse"})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["review"]
        assert data["scores"] == WORKER_SCORES
        assert data["overall"] == "4.33"
        assert data["author_name"] == "Jean I."
        assert Review.objects.get().target == match.worker.user

    def test_travailleur_evalue_le_client(self, match):
        response = review(match.worker.user, match, CLIENT_SCORES)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["review"]["scores"] == CLIENT_SCORES
        assert response.data["review"]["overall"] == "4.00"

    def test_une_seule_evaluation_par_personne(self, match):
        review(match.client.user, match, WORKER_SCORES)
        response = review(match.client.user, match, WORKER_SCORES)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Review.objects.count() == 1

    def test_trop_tot_avant_la_fin_de_l_essai(self, recent_match):
        response = review(recent_match.client.user, recent_match, WORKER_SCORES)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "à partir du" in response.data["detail"]

    def test_impossible_sans_match_mutuel(self, match):
        Match.objects.filter(pk=match.pk).update(first_mutual_at=None)
        response = review(match.client.user, match, WORKER_SCORES)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_possible_meme_si_l_autre_s_est_retire(self, match):
        """Un essai qui s'est mal passé doit pouvoir être évalué."""
        match.set_decision(match.client.user, Match.DECISION_DECLINED)
        response = review(match.client.user, match, WORKER_SCORES)
        assert response.status_code == status.HTTP_201_CREATED

    def test_critere_manquant(self, match):
        response = review(match.client.user, match, {"punctuality": 5, "competence": 4})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "reliability" in response.data

    def test_mauvais_criteres_pour_le_role(self, match):
        response = review(match.client.user, match, {**WORKER_SCORES, "respect": 5})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "respect" in response.data

    def test_note_hors_limites(self, match):
        response = review(match.client.user, match, {**WORKER_SCORES, "competence": 6})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_un_tiers_ne_peut_pas_evaluer(self, match):
        stranger = User.objects.create_user(phone="+243866009999", role=User.ROLE_CLIENT)
        assert review(stranger, match, WORKER_SCORES).status_code == status.HTTP_404_NOT_FOUND

    def test_sans_token_retourne_401(self, match):
        response = APIClient().post(reverse("matches-review", args=[match.id]), WORKER_SCORES)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : informations dans la liste des matchs                       #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestMatchReviewInfo:
    def test_can_review_selon_le_delai(self, match, recent_match):
        [m] = auth_client(match.client.user).get(reverse("matches-list")).data["results"]
        assert m["can_review"] is True
        [m] = auth_client(recent_match.client.user).get(reverse("matches-list")).data["results"]
        assert m["can_review"] is False
        assert m["review_available_at"] is not None

    def test_can_review_faux_apres_evaluation(self, match):
        review(match.client.user, match, WORKER_SCORES)
        [m] = auth_client(match.client.user).get(reverse("matches-list")).data["results"]
        assert m["can_review"] is False


# ------------------------------------------------------------------ #
# Tests : affichage public et moyennes                                #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestPublicReviews:
    def test_moyenne_et_nombre_d_avis_sur_le_profil_travailleur(self, match):
        other = make_match(3)
        # Le même travailleur reçoit deux avis : on rattache le 2e match à lui
        Match.objects.filter(pk=other.pk).update(worker=match.worker)
        other.refresh_from_db()
        review(match.client.user, match, {"punctuality": 5, "competence": 5, "reliability": 5})
        review(other.client.user, other, {"punctuality": 4, "competence": 4, "reliability": 4})

        profiles = auth_client(match.client.user).get(reverse("workers-list")).data["results"]
        rating = next(p for p in profiles if p["id"] == match.worker.id)["rating"]
        assert rating == {"average": "4.5", "count": 2}

    def test_profil_sans_avis(self, match):
        profiles = auth_client(match.client.user).get(reverse("workers-list")).data["results"]
        assert profiles[0]["rating"] == {"average": None, "count": 0}

    def test_liste_des_avis_d_un_travailleur(self, match):
        review(match.client.user, match, {**WORKER_SCORES, "comment": "Très sérieuse"})
        url = reverse("reviews-worker", args=[match.worker.id])
        data = auth_client(match.client.user).get(url).data
        assert data["summary"]["count"] == 1
        assert data["summary"]["criteria"]["punctuality"] == 5
        [item] = data["results"]
        assert item["comment"] == "Très sérieuse"
        # L'auteur n'apparaît qu'avec l'initiale de son nom, sans téléphone
        assert item["author_name"] == "Jean I."
        assert "Ilunga" not in str(data)
        assert str(match.client.user.phone) not in str(data)

    def test_liste_des_avis_d_un_client(self, match):
        review(match.worker.user, match, CLIENT_SCORES)
        url = reverse("reviews-client", args=[match.client.id])
        data = auth_client(match.worker.user).get(url).data
        assert data["summary"]["criteria"] == {"respect": 5.0, "clarity": 3.0, "payment_on_time": 4.0}
        assert data["results"][0]["author_name"] == "Grace M."

    def test_commentaire_retire_par_la_moderation(self, match):
        review(match.client.user, match, {**WORKER_SCORES, "comment": "Propos déplacés"})
        Review.objects.update(comment_hidden=True)
        url = reverse("reviews-worker", args=[match.worker.id])
        data = auth_client(match.client.user).get(url).data
        assert data["results"][0]["comment"] == "Ce commentaire a été retiré par la modération."
        # La note reste comptée
        assert data["summary"]["count"] == 1

    def test_profil_inexistant_retourne_404(self, match):
        url = reverse("reviews-worker", args=[99999])
        assert auth_client(match.client.user).get(url).status_code == status.HTTP_404_NOT_FOUND
