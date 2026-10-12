"""
Tests de l'app reports.
Couvre : signalement (catégories, visibilité, doublons, anonymat), décisions de
l'administrateur (sans suite, avertissement, suspension) et leurs effets.
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
from apps.reports.models import Report
from apps.workers.models import WorkerProfile
from common import choices

URL = reverse("reports")
CLIENT_PHONE = "+243812300001"
WORKER_PHONE = "+243812300002"


# ------------------------------------------------------------------ #
# Helpers & fixtures                                                   #
# ------------------------------------------------------------------ #

def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def report(user, profile_id, category="arnaque", description="Demande de l'argent d'avance"):
    return auth_client(user).post(
        URL, {"profile_id": profile_id, "category": category, "description": description}, format="json"
    )


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
        user=user, first_name="Jean", last_name="Ilunga",
        location="Golf", availability_needed=choices.AVAILABILITY_FULL,
    )


@pytest.fixture
def worker(db):
    return make_worker(WORKER_PHONE)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(phone="+243877000099", password="x")


# ------------------------------------------------------------------ #
# Tests : envoyer un signalement                                      #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestCreateReport:
    def test_client_signale_un_travailleur(self, client_profile, worker):
        response = report(client_profile.user, worker.id)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["report"]["status"] == "en_attente"
        saved = Report.objects.get()
        assert saved.reporter == client_profile.user
        assert saved.target == worker.user

    def test_travailleur_signale_un_client(self, client_profile, worker):
        response = report(worker.user, client_profile.id, category="comportement_inapproprie")
        assert response.status_code == status.HTTP_201_CREATED

    def test_sans_match_necessaire(self, client_profile, worker):
        assert not Match.objects.exists()
        assert report(client_profile.user, worker.id).status_code == status.HTTP_201_CREATED

    def test_description_obligatoire_pour_autre(self, client_profile, worker):
        response = report(client_profile.user, worker.id, category="autre", description="")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "description" in response.data

    def test_description_facultative_pour_les_autres_categories(self, client_profile, worker):
        response = report(client_profile.user, worker.id, category="faux_profil", description="")
        assert response.status_code == status.HTTP_201_CREATED

    def test_categorie_inconnue(self, client_profile, worker):
        response = report(client_profile.user, worker.id, category="spam")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pas_de_doublon_en_attente(self, client_profile, worker):
        report(client_profile.user, worker.id)
        assert report(client_profile.user, worker.id).status_code == status.HTTP_400_BAD_REQUEST

    def test_travailleur_non_visible_ne_peut_pas_etre_signale(self, client_profile):
        hidden = make_worker("+243877000003", verified=False)
        assert report(client_profile.user, hidden.id).status_code == status.HTTP_404_NOT_FOUND

    def test_travailleur_non_verifie_mais_en_relation_peut_etre_signale(self, client_profile):
        worker = make_worker("+243877000004", verified=False)
        Match.objects.create(client=client_profile, worker=worker)
        assert report(client_profile.user, worker.id).status_code == status.HTTP_201_CREATED

    def test_sans_token_retourne_401(self, worker):
        response = APIClient().post(URL, {"profile_id": worker.id, "category": "arnaque"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auteur_voit_seulement_en_attente_ou_traite(self, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        Report.objects.get().decide(admin_user, Report.STATUS_SUSPENDED)
        [item] = auth_client(client_profile.user).get(URL).data["results"]
        assert item["status"] == "traite"


# ------------------------------------------------------------------ #
# Tests : décisions de l'administrateur                               #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestDecisions:
    def test_avertissement_visible_par_la_personne_sans_l_auteur(self, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        Report.objects.get().decide(admin_user, Report.STATUS_WARNED, "Merci de rester courtoise.")
        me = auth_client(worker.user).get(reverse("accounts-me")).data
        assert me["warnings"][0]["message"] == "Merci de rester courtoise."
        # Anonymat : rien ne permet d'identifier l'auteur du signalement
        assert CLIENT_PHONE not in str(me)
        assert "Jean" not in str(me)

    def test_avertissement_avec_message_par_defaut(self, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        Report.objects.get().decide(admin_user, Report.STATUS_WARNED)
        me = auth_client(worker.user).get(reverse("accounts-me")).data
        assert "signalement" in me["warnings"][0]["message"]

    def test_classe_sans_suite_n_a_aucun_effet(self, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        Report.objects.get().decide(admin_user, Report.STATUS_DISMISSED)
        worker.user.refresh_from_db()
        assert worker.user.is_active is True
        assert auth_client(worker.user).get(reverse("accounts-me")).data["warnings"] == []


# ------------------------------------------------------------------ #
# Tests : effets d'une suspension                                     #
# ------------------------------------------------------------------ #

@pytest.fixture
def suspended_worker(client_profile, worker, admin_user):
    report(client_profile.user, worker.id)
    Report.objects.get().decide(admin_user, Report.STATUS_SUSPENDED)
    worker.user.refresh_from_db()
    return worker


@pytest.mark.django_db
class TestSuspension:
    def test_compte_desactive(self, suspended_worker):
        assert suspended_worker.user.is_active is False

    def test_connexion_impossible(self, suspended_worker):
        api = APIClient()
        # La demande de code ne révèle rien ; la suspension est annoncée après un code
        # correct, donc seulement au titulaire du numéro
        response = api.post(reverse("accounts-otp-request"), {"phone": WORKER_PHONE}, format="json")
        assert response.status_code == status.HTTP_200_OK
        response = api.post(
            reverse("accounts-otp-verify"), {"phone": WORKER_PHONE, "code": "123456"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "suspendu" in str(response.data)
        assert "tokens" not in response.data

    def test_ancien_token_refuse(self, suspended_worker):
        response = auth_client(suspended_worker.user).get(reverse("accounts-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_disparait_de_la_liste_des_travailleurs(self, suspended_worker, client_profile):
        results = auth_client(client_profile.user).get(reverse("workers-list")).data["results"]
        assert results == []

    def test_client_suspendu_disparait_de_la_liste_des_clients(self, client_profile, worker, admin_user):
        report(worker.user, client_profile.id)
        Report.objects.get().decide(admin_user, Report.STATUS_SUSPENDED)
        assert auth_client(worker.user).get(reverse("clients-list")).data["results"] == []

    def test_disparait_des_matchs_et_de_la_messagerie(self, client_profile, worker, admin_user):
        match = Match.objects.create(client=client_profile, worker=worker)
        match.set_decision(client_profile.user, Match.DECISION_INTERESTED)
        match.set_decision(worker.user, Match.DECISION_INTERESTED)
        report(client_profile.user, worker.id)
        Report.objects.get().decide(admin_user, Report.STATUS_SUSPENDED)

        api = auth_client(client_profile.user)
        assert api.get(reverse("matches-list")).data["results"] == []
        url = reverse("messages-conversation", args=[match.id])
        assert api.post(url, {"content": "Bonjour"}, format="json").status_code == 404

    def test_impossible_de_manifester_un_interet(self, suspended_worker, client_profile):
        response = auth_client(client_profile.user).post(
            reverse("matches-interest"), {"profile_id": suspended_worker.id}, format="json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_annuler_la_suspension_reactive_le_compte(self, suspended_worker, admin_user):
        Report.objects.get().decide(admin_user, Report.STATUS_DISMISSED)
        suspended_worker.user.refresh_from_db()
        assert suspended_worker.user.is_active is True

    def test_reste_suspendu_si_un_autre_signalement_le_maintient(self, suspended_worker, admin_user):
        other_client = User.objects.create_user(phone="+243877000005", role=User.ROLE_CLIENT, phone_verified=True)
        Report.objects.create(
            reporter=other_client, target=suspended_worker.user,
            category=Report.CATEGORY_SCAM, status=Report.STATUS_SUSPENDED,
        )
        first = Report.objects.filter(reporter__phone=CLIENT_PHONE).get()
        first.decide(admin_user, Report.STATUS_DISMISSED)
        suspended_worker.user.refresh_from_db()
        assert suspended_worker.user.is_active is False


# ------------------------------------------------------------------ #
# Tests : interface admin                                              #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestAdmin:
    @pytest.fixture(autouse=True)
    def hosts(self, settings):
        settings.ALLOWED_HOSTS = ["*"]

    def test_suspendre_via_le_formulaire(self, client, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        saved = Report.objects.get()
        client.force_login(admin_user)
        url = reverse("admin:reports_report_change", args=[saved.pk])
        assert client.get(url).status_code == 200
        response = client.post(url, {"status": "suspendu", "user_message": "", "admin_note": "Arnaque avérée"})
        assert response.status_code == 302
        saved.refresh_from_db()
        worker.user.refresh_from_db()
        assert saved.decided_by == admin_user
        assert worker.user.is_active is False

    def test_lever_la_suspension_via_le_formulaire(self, client, suspended_worker, admin_user):
        client.force_login(admin_user)
        url = reverse("admin:reports_report_change", args=[Report.objects.get().pk])
        client.post(url, {"status": "classe_sans_suite", "user_message": "", "admin_note": ""})
        suspended_worker.user.refresh_from_db()
        assert suspended_worker.user.is_active is True

    def test_liste_des_signalements(self, client, client_profile, worker, admin_user):
        report(client_profile.user, worker.id)
        client.force_login(admin_user)
        assert client.get(reverse("admin:reports_report_changelist")).status_code == 200


@pytest.mark.django_db
class TestSignalementParUnTravailleurNonVerifie:
    """Test d'intrusion d'octobre 2026 : pas de sondage des familles par les signalements."""

    def test_famille_inconnue_refusee(self, client_profile):
        unverified = make_worker("+243877000050", verified=False)
        assert report(unverified.user, client_profile.id).status_code == status.HTTP_404_NOT_FOUND
        assert not Report.objects.exists()

    def test_famille_deja_en_relation_acceptee(self, client_profile):
        unverified = make_worker("+243877000051", verified=False)
        Match.objects.create(client=client_profile, worker=unverified)
        assert report(unverified.user, client_profile.id).status_code == status.HTTP_201_CREATED
