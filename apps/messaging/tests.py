"""
Tests de l'app messaging.
Couvre : envoi et lecture dans un match mutuel, fermeture hors match mutuel,
messages non lus, modération, permissions.
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
from apps.messaging.models import Message
from apps.workers.models import WorkerProfile
from common import choices


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def url(match):
    return reverse("messages-conversation", args=[match.id])


def send(user, match, content="Bonjour !"):
    return auth_client(user).post(url(match), {"content": content}, format="json")


def read(user, match):
    return auth_client(user).get(url(match))


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def match(db):
    """Match mutuel entre un client et un travailleur vérifié."""
    client_user = User.objects.create_user(phone="+243844000001", role=User.ROLE_CLIENT)
    worker_user = User.objects.create_user(phone="+243844000002", role=User.ROLE_WORKER)
    client = ClientProfile.objects.create(
        user=client_user,
        first_name="Jean",
        last_name="Ilunga",
        location="Golf",
        availability_needed=choices.AVAILABILITY_FULL,
    )
    worker = WorkerProfile.objects.create(
        user=worker_user,
        first_name="Grace",
        last_name="Mutombo",
        availability=choices.AVAILABILITY_FULL,
        expected_salary=Decimal("200.00"),
        location="Annexe",
        is_verified=True,
    )
    match = Match.objects.create(client=client, worker=worker)
    match.set_decision(client_user, Match.DECISION_INTERESTED)
    match.set_decision(worker_user, Match.DECISION_INTERESTED)
    return match


@pytest.fixture
def client_user(match):
    return match.client.user


@pytest.fixture
def worker_user(match):
    return match.worker.user


# ------------------------------------------------------------------ #
# Tests : conversation dans un match mutuel                           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestConversation:
    def test_client_envoie_un_message(self, match, client_user):
        response = send(client_user, match, "Bonjour Grace, êtes-vous disponible ?")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_mine"] is True
        assert Message.objects.filter(match=match, sender=client_user).count() == 1

    def test_les_deux_participants_lisent_la_conversation(self, match, client_user, worker_user):
        send(client_user, match, "Bonjour")
        send(worker_user, match, "Bonjour, oui je suis disponible")

        messages = read(worker_user, match).data["results"]
        assert [m["content"] for m in messages] == ["Bonjour", "Bonjour, oui je suis disponible"]
        assert [m["is_mine"] for m in messages] == [False, True]

    def test_message_vide_refuse(self, match, client_user):
        response = send(client_user, match, "   ")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_message_trop_long_refuse(self, match, client_user):
        response = send(client_user, match, "a" * 2001)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------------------------------------------ #
# Tests : messages non lus                                            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestUnread:
    def test_compteur_non_lus_dans_la_liste_des_matchs(self, match, client_user, worker_user):
        send(client_user, match, "Message 1")
        send(client_user, match, "Message 2")
        matches = auth_client(worker_user).get(reverse("matches-list")).data["results"]
        assert matches[0]["unread_count"] == 2
        # Ses propres messages ne comptent pas comme non lus
        matches = auth_client(client_user).get(reverse("matches-list")).data["results"]
        assert matches[0]["unread_count"] == 0

    def test_lecture_marque_les_messages_comme_lus(self, match, client_user, worker_user):
        send(client_user, match)
        read(worker_user, match)
        assert Message.objects.get().read_at is not None
        matches = auth_client(worker_user).get(reverse("matches-list")).data["results"]
        assert matches[0]["unread_count"] == 0

    def test_lecture_par_l_expediteur_ne_marque_pas_comme_lu(self, match, client_user):
        send(client_user, match)
        read(client_user, match)
        assert Message.objects.get().read_at is None


# ------------------------------------------------------------------ #
# Tests : messagerie fermée hors match mutuel                         #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestClosedConversation:
    def test_impossible_d_ecrire_avant_match_mutuel(self, match, client_user, worker_user):
        match.set_decision(worker_user, Match.DECISION_PENDING)
        response = send(client_user, match)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_conversation_fermee_apres_refus(self, match, client_user, worker_user):
        send(client_user, match)
        match.set_decision(worker_user, Match.DECISION_DECLINED)
        assert read(client_user, match).status_code == status.HTTP_403_FORBIDDEN
        assert send(worker_user, match).status_code == status.HTTP_403_FORBIDDEN

    def test_un_tiers_ne_peut_pas_lire(self, match):
        stranger = User.objects.create_user(phone="+243844000009", role=User.ROLE_CLIENT)
        assert read(stranger, match).status_code == status.HTTP_404_NOT_FOUND
        assert send(stranger, match).status_code == status.HTTP_404_NOT_FOUND

    def test_sans_token_retourne_401(self, match):
        response = APIClient().get(url(match))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : modération                                                   #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestModeration:
    def test_message_retire_n_affiche_plus_son_contenu(self, match, client_user, worker_user):
        send(client_user, match, "Contenu inapproprié")
        Message.objects.update(is_hidden=True)
        [message] = read(worker_user, match).data["results"]
        assert message["is_hidden"] is True
        assert "inapproprié" not in message["content"]
        assert message["content"] == "Ce message a été retiré par la modération."
