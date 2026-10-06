"""
Tests de l'app verification.
Couvre : envoi de documents, contrôles (format, taille, doublons), confidentialité,
décision de l'administrateur et badge « vérifié ».
"""
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.verification.models import VerificationRecord
from apps.workers.models import WorkerProfile
from common import choices

URL = reverse("verification-documents")


# ------------------------------------------------------------------ #
# Helpers & fixtures                                                   #
# ------------------------------------------------------------------ #

@pytest.fixture(autouse=True)
def media_in_tmp(settings, tmp_path):
    """Les fichiers de test sont écrits dans un dossier temporaire, jamais dans media/."""
    settings.MEDIA_ROOT = tmp_path


def auth_client(user) -> APIClient:
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def pdf(name="carte.pdf", size=100):
    return SimpleUploadedFile(name, b"%PDF-1.4 " + b"0" * size, content_type="application/pdf")


def upload(user, doc_type="identite", file=None):
    return auth_client(user).post(
        URL, {"doc_type": doc_type, "file": file or pdf()}, format="multipart"
    )


@pytest.fixture
def worker(db):
    user = User.objects.create_user(phone="+243855000001", role=User.ROLE_WORKER)
    return WorkerProfile.objects.create(
        user=user,
        first_name="Grace",
        last_name="Mutombo",
        availability=choices.AVAILABILITY_FULL,
        expected_salary=Decimal("200.00"),
        location="Annexe",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(phone="+243855000099", password="x")


# ------------------------------------------------------------------ #
# Tests : envoi de documents                                           #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestUpload:
    def test_travailleur_envoie_sa_piece_d_identite(self, worker):
        response = upload(worker.user)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["document"]["status"] == "en_attente"
        record = VerificationRecord.objects.get()
        assert record.worker == worker
        # Le nom d'origine du fichier n'est pas conservé
        assert "carte" not in record.file.name

    def test_le_fichier_n_est_jamais_renvoye(self, worker):
        upload(worker.user)
        data = auth_client(worker.user).get(URL).data
        assert "file" not in data["documents"][0]
        assert data["is_verified"] is False

    def test_format_non_accepte(self, worker):
        file = SimpleUploadedFile("script.exe", b"MZ", content_type="application/octet-stream")
        assert upload(worker.user, file=file).status_code == status.HTTP_400_BAD_REQUEST

    def test_fichier_trop_volumineux(self, worker):
        response = upload(worker.user, file=pdf(size=5 * 1024 * 1024 + 1))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_type_inconnu_refuse(self, worker):
        assert upload(worker.user, doc_type="diplome").status_code == status.HTTP_400_BAD_REQUEST

    def test_pas_de_doublon_en_attente(self, worker):
        upload(worker.user)
        assert upload(worker.user).status_code == status.HTTP_400_BAD_REQUEST

    def test_reference_en_plus_de_l_identite(self, worker):
        upload(worker.user)
        assert upload(worker.user, doc_type="reference").status_code == status.HTTP_201_CREATED

    def test_nouvel_envoi_possible_apres_rejet(self, worker, admin_user):
        upload(worker.user)
        VerificationRecord.objects.get().review(admin_user, VerificationRecord.STATUS_REJECTED, "Flou")
        assert upload(worker.user).status_code == status.HTTP_201_CREATED

    def test_profil_obligatoire(self, db):
        user = User.objects.create_user(phone="+243855000002", role=User.ROLE_WORKER)
        assert upload(user).status_code == status.HTTP_404_NOT_FOUND

    def test_client_refuse(self, db):
        user = User.objects.create_user(phone="+243855000003", role=User.ROLE_CLIENT)
        assert upload(user).status_code == status.HTTP_403_FORBIDDEN

    def test_sans_token_retourne_401(self):
        response = APIClient().post(URL, {"doc_type": "identite", "file": pdf()}, format="multipart")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : décision de l'admin et badge « vérifié »                    #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestReviewAndBadge:
    def test_validation_identite_accorde_le_badge(self, worker, admin_user):
        upload(worker.user)
        VerificationRecord.objects.get().review(admin_user, VerificationRecord.STATUS_APPROVED)
        worker.refresh_from_db()
        assert worker.is_verified is True
        assert auth_client(worker.user).get(URL).data["is_verified"] is True

    def test_validation_reference_seule_n_accorde_pas_le_badge(self, worker, admin_user):
        upload(worker.user, doc_type="reference")
        VerificationRecord.objects.get().review(admin_user, VerificationRecord.STATUS_APPROVED)
        worker.refresh_from_db()
        assert worker.is_verified is False

    def test_rejet_visible_avec_son_motif(self, worker, admin_user):
        upload(worker.user)
        VerificationRecord.objects.get().review(
            admin_user, VerificationRecord.STATUS_REJECTED, "Photo illisible"
        )
        document = auth_client(worker.user).get(URL).data["documents"][0]
        assert document["status"] == "rejete"
        assert document["rejection_reason"] == "Photo illisible"

    def test_annuler_la_validation_retire_le_badge(self, worker, admin_user):
        upload(worker.user)
        record = VerificationRecord.objects.get()
        record.review(admin_user, VerificationRecord.STATUS_APPROVED)
        record.review(admin_user, VerificationRecord.STATUS_REJECTED, "Document falsifié")
        worker.refresh_from_db()
        assert worker.is_verified is False

    def test_suppression_efface_le_fichier(self, worker):
        upload(worker.user)
        record = VerificationRecord.objects.get()
        storage, name = record.file.storage, record.file.name
        assert storage.exists(name)
        record.delete()
        assert not storage.exists(name)


# ------------------------------------------------------------------ #
# Tests : interface admin                                              #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestAdmin:
    @pytest.fixture(autouse=True)
    def hosts(self, settings):
        settings.ALLOWED_HOSTS = ["*"]

    def test_admin_ouvre_le_document(self, client, worker, admin_user):
        upload(worker.user)
        record = VerificationRecord.objects.get()
        client.force_login(admin_user)
        url = reverse("admin:verification_verificationrecord_file", args=[record.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert b"".join(response.streaming_content).startswith(b"%PDF")

    def test_document_inaccessible_hors_admin(self, client, worker):
        upload(worker.user)
        record = VerificationRecord.objects.get()
        client.force_login(worker.user)  # connecté mais pas administrateur
        url = reverse("admin:verification_verificationrecord_file", args=[record.pk])
        response = client.get(url)
        assert response.status_code == 302  # redirigé vers la page de connexion admin

    def test_admin_valide_via_le_formulaire(self, client, worker, admin_user):
        upload(worker.user)
        record = VerificationRecord.objects.get()
        client.force_login(admin_user)
        url = reverse("admin:verification_verificationrecord_change", args=[record.pk])
        assert client.get(url).status_code == 200
        response = client.post(url, {"status": "valide", "rejection_reason": ""})
        assert response.status_code == 302
        record.refresh_from_db()
        worker.refresh_from_db()
        assert record.status == "valide"
        assert record.reviewed_by == admin_user
        assert worker.is_verified is True

    def test_admin_action_valider_en_masse(self, client, worker, admin_user):
        upload(worker.user)
        client.force_login(admin_user)
        client.post(
            reverse("admin:verification_verificationrecord_changelist"),
            {"action": "approve_documents", "_selected_action": [VerificationRecord.objects.get().pk]},
        )
        worker.refresh_from_db()
        assert worker.is_verified is True
