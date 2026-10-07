"""
Tests de l'app notifications.
Couvre : intérêt reçu, match, messages regroupés, refus jamais notifié,
documents / références / avertissements, lecture et confidentialité.
"""
import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.matching.tests import auth_client, client_profile, decline, interest, worker_profile  # noqa: F401
from apps.notifications.models import Notification
from apps.reports.models import Report


def kinds(user):
    return list(Notification.objects.filter(user=user).values_list("kind", flat=True))


@pytest.mark.django_db
class TestNotifications:
    def test_interet_recu_avec_nom_masque(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        notification = Notification.objects.get(user=worker_profile.user)
        assert notification.kind == "interest_received"
        assert notification.params["name"] == "Jean I."  # pas le nom complet avant le match
        assert kinds(client_profile.user) == []

    def test_match_mutuel_avec_nom_complet(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        interest(worker_profile.user, client_profile.id)
        match_notification = Notification.objects.get(user=client_profile.user, kind="match_mutual")
        assert match_notification.params["name"] == "Grace Mutombo"

    def test_interet_repete_ne_notifie_pas_deux_fois(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        interest(client_profile.user, worker_profile.id)
        assert kinds(worker_profile.user) == ["interest_received"]

    def test_refus_jamais_notifie(self, client_profile, worker_profile):
        response = interest(client_profile.user, worker_profile.id)
        decline(worker_profile.user, response.data["match"]["id"])
        assert kinds(client_profile.user) == []
        # Et si la famille insiste, la personne qui a refusé n'est pas relancée
        Notification.objects.all().delete()
        interest(client_profile.user, worker_profile.id)
        assert kinds(worker_profile.user) == []

    def test_messages_regroupes(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        match_id = interest(worker_profile.user, client_profile.id).data["match"]["id"]
        url = reverse("messages-conversation", args=[match_id])
        for text in ["Bonjour", "Êtes-vous disponible ?", "Merci"]:
            auth_client(client_profile.user).post(url, {"content": text}, format="json")
        messages = Notification.objects.filter(user=worker_profile.user, kind="new_message")
        assert messages.count() == 1
        assert messages.get().count == 3
        assert messages.get().params["name"] == "Jean Ilunga"

    def test_liste_compteur_et_lecture(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        api = auth_client(worker_profile.user)
        assert api.get(reverse("notifications-unread-count")).data == {"unread": 1}
        page = api.get(reverse("notifications-list")).data
        assert page["count"] == 1 and page["results"][0]["is_read"] is False
        api.post(reverse("notifications-read"), {}, format="json")
        assert api.get(reverse("notifications-unread-count")).data == {"unread": 0}

    def test_on_ne_voit_que_ses_notifications(self, client_profile, worker_profile):
        interest(client_profile.user, worker_profile.id)
        other = Notification.objects.get().id
        api = auth_client(client_profile.user)
        assert api.get(reverse("notifications-list")).data["count"] == 0
        api.post(reverse("notifications-read"), {"ids": [other]}, format="json")
        assert Notification.objects.get().read_at is None

    def test_avertissement_notifie(self, client_profile, worker_profile):
        admin = User.objects.create_superuser(phone="+243833000099", password="x")
        report = Report.objects.create(
            reporter=client_profile.user, target=worker_profile.user, category="autre", description="…"
        )
        report.decide(admin, Report.STATUS_WARNED)
        assert kinds(worker_profile.user) == ["warning"]
