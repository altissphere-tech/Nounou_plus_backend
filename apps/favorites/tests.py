"""
Tests de l'app favoris.
"""
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.jobs.models import JobRequest
from apps.matching.tests import _make_worker, auth_client, client_profile, worker_profile  # noqa: F401
from apps.services.models import Service
from common import choices


@pytest.fixture
def job(client_profile):
    return JobRequest.objects.create(
        client=client_profile,
        title="Nounou pour deux enfants",
        service=Service.objects.get(slug="nounou"),
        availability=choices.AVAILABILITY_FULL,
        budget=Decimal("300000"),
        location="Golf",
    )


@pytest.mark.django_db
class TestFavorites:
    def test_famille_ajoute_et_retire_un_travailleur(self, client_profile, worker_profile):
        api = auth_client(client_profile.user)
        url = reverse("favorites-worker", args=[worker_profile.id])
        assert api.put(url).status_code == 200
        assert api.put(url).status_code == 200  # deux fois : pas de doublon
        favorites = api.get(reverse("favorites-list")).data
        assert [w["id"] for w in favorites["workers"]] == [worker_profile.id]
        assert favorites["workers"][0]["last_name"] == "M."  # mêmes règles que la recherche
        assert api.delete(url).status_code == 200
        assert api.get(reverse("favorites-list")).data["workers"] == []

    def test_travailleur_non_verifie_impossible(self, client_profile):
        unverified = _make_worker("+243833000005", verified=False)
        api = auth_client(client_profile.user)
        assert api.put(reverse("favorites-worker", args=[unverified.id])).status_code == 404

    def test_travailleur_qui_perd_son_badge_disparait(self, client_profile, worker_profile):
        api = auth_client(client_profile.user)
        api.put(reverse("favorites-worker", args=[worker_profile.id]))
        worker_profile.is_verified = False
        worker_profile.save()
        assert api.get(reverse("favorites-list")).data["workers"] == []

    def test_travailleur_met_une_annonce_de_cote(self, worker_profile, job):
        api = auth_client(worker_profile.user)
        assert api.put(reverse("favorites-job", args=[job.id])).status_code == 200
        assert [j["id"] for j in api.get(reverse("favorites-list")).data["jobs"]] == [job.id]
        job.status = JobRequest.STATUS_CLOSED
        job.save()
        assert api.get(reverse("favorites-list")).data["jobs"] == []

    def test_roles(self, client_profile, worker_profile, job):
        as_worker = auth_client(worker_profile.user).put(reverse("favorites-worker", args=[worker_profile.id]))
        as_client = auth_client(client_profile.user).put(reverse("favorites-job", args=[job.id]))
        assert as_worker.status_code == as_client.status_code == 403
