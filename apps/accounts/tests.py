"""
Tests de l'app accounts.

Chaque test vérifie un scénario critique : inscription, OTP, connexion, profil.
On utilise pytest + pytest-django (plus simple et plus rapide que le TestCase de Django).
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User


# ------------------------------------------------------------------ #
# Fixtures — données réutilisables dans tous les tests               #
# ------------------------------------------------------------------ #

@pytest.fixture
def api_client():
    """Client HTTP pour simuler des appels à l'API."""
    return APIClient()


@pytest.fixture
def registered_user(db):
    """Crée un utilisateur en base et génère son OTP."""
    user = User.objects.create_user(phone="+243812345678", role=User.ROLE_CLIENT)
    user.generate_otp()
    return user


@pytest.fixture
def authenticated_client(api_client, registered_user):
    """Client HTTP avec un token JWT valide (utilisateur déjà connecté)."""
    # On vérifie l'OTP pour obtenir un token
    response = api_client.post(
        reverse("accounts-otp-verify"),
        {"phone": "+243812345678", "code": "123456"},
        format="json",
    )
    token = response.data["tokens"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ------------------------------------------------------------------ #
# Tests d'inscription                                                  #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestRegister:
    def test_inscription_client_reussie(self, api_client):
        """Un client peut créer un compte avec un numéro valide."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812345678", "role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" not in response.data  # la réponse ne décrit aucun compte (voir doublon)
        assert User.objects.get(phone="+243812345678").role == "client"

    def test_inscription_travailleur_reussie(self, api_client):
        """Un travailleur peut créer un compte avec un numéro valide."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243897654321", "role": "travailleur"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.get(phone="+243897654321").role == "travailleur"

    def test_inscription_doublon_sans_indice(self, api_client, registered_user):
        """
        Un numéro déjà inscrit : pas de second compte, mais la même réponse qu'une
        inscription (on ne révèle pas qui est inscrit). Le titulaire reçoit un code.
        """
        new = api_client.post(reverse("accounts-register"), {"phone": "+243899000111", "role": "client"}, format="json")
        registered_user.otp_code = None
        registered_user.save()
        dup = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812345678", "role": "travailleur"},
            format="json",
        )
        assert dup.status_code == new.status_code == status.HTTP_201_CREATED
        assert dup.data == new.data
        assert User.objects.filter(phone="+243812345678").count() == 1
        registered_user.refresh_from_db()
        assert registered_user.role == "client" and registered_user.otp_code

    def test_inscription_role_admin_interdit(self, api_client):
        """Le rôle 'admin' ne peut pas être choisi lors de l'inscription via l'API."""
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243811111111", "role": "admin"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inscription_sans_telephone_echoue(self, api_client):
        """L'inscription échoue si le numéro de téléphone est absent."""
        response = api_client.post(
            reverse("accounts-register"),
            {"role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------------------------------------------ #
# Tests OTP                                                            #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestOTP:
    def test_demande_otp_valide(self, api_client, registered_user):
        """La demande d'OTP réussit pour un numéro existant."""
        response = api_client.post(
            reverse("accounts-otp-request"),
            {"phone": "+243812345678"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_demande_otp_numero_inconnu_sans_indice(self, api_client, registered_user):
        """Numéro inconnu : même réponse qu'un numéro inscrit (pas d'énumération des comptes)."""
        unknown = api_client.post(reverse("accounts-otp-request"), {"phone": "+243899999999"}, format="json")
        known = api_client.post(reverse("accounts-otp-request"), {"phone": "+243812345678"}, format="json")
        assert unknown.status_code == known.status_code == status.HTTP_200_OK
        assert unknown.data == known.data
        unknown_verify = api_client.post(
            reverse("accounts-otp-verify"), {"phone": "+243899999999", "code": "123456"}, format="json"
        )
        wrong_code = api_client.post(
            reverse("accounts-otp-verify"), {"phone": "+243812345678", "code": "000000"}, format="json"
        )
        assert unknown_verify.data == wrong_code.data

    def test_verification_otp_correcte(self, api_client, registered_user):
        """Un code OTP correct retourne des tokens JWT."""
        response = api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "123456"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_verification_otp_incorrecte(self, api_client, registered_user):
        """Un code OTP incorrect est refusé."""
        response = api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "000000"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_telephone_marque_verifie_apres_otp(self, api_client, registered_user):
        """Après vérification OTP réussie, phone_verified passe à True."""
        api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345678", "code": "123456"},
            format="json",
        )
        registered_user.refresh_from_db()
        assert registered_user.phone_verified is True


# ------------------------------------------------------------------ #
# Tests profil /me/                                                    #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestMe:
    def test_profil_accessible_avec_token(self, authenticated_client):
        """Un utilisateur connecté peut accéder à son profil."""
        response = authenticated_client.get(reverse("accounts-me"))
        assert response.status_code == status.HTTP_200_OK
        assert "phone" in response.data
        assert "role" in response.data

    def test_profil_inaccessible_sans_token(self, api_client):
        """Sans token JWT, /me/ retourne 401."""
        response = api_client.get(reverse("accounts-me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------ #
# Tests : OTP simulé désactivé (comportement en production)          #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
class TestOTPMockDisabled:
    @pytest.fixture(autouse=True)
    def disable_mock(self, settings):
        settings.OTP_MOCK_ENABLED = False

    def test_inscription_refusee_sans_service_otp(self, api_client):
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812345679", "role": "client"},
            format="json",
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        # Le compte ne doit pas avoir été créé
        assert not User.objects.filter(phone="+243812345679").exists()

    def test_demande_otp_refusee(self, api_client):
        User.objects.create_user(phone="+243812345679", role=User.ROLE_CLIENT)
        response = api_client.post(
            reverse("accounts-otp-request"), {"phone": "+243812345679"}, format="json"
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_code_123456_refuse(self, api_client):
        user = User.objects.create_user(phone="+243812345679", role=User.ROLE_CLIENT)
        # Même si un ancien code simulé est resté en base, il est refusé
        user.otp_code = User.OTP_MOCK_CODE
        user.save()
        response = api_client.post(
            reverse("accounts-otp-verify"),
            {"phone": "+243812345679", "code": "123456"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------------------------------------------ #
# Test : commande de démonstration du parcours complet                #
# ------------------------------------------------------------------ #

@pytest.mark.django_db
def test_commande_demo_parcours(settings, tmp_path):
    from io import StringIO

    from django.core.management import call_command

    settings.MEDIA_ROOT = tmp_path
    users_before = User.objects.count()
    out = StringIO()
    call_command("demo_parcours", stdout=out)
    assert "Démo terminée avec succès" in out.getvalue()
    # Sans --garder, toutes les données de démo sont effacées
    assert User.objects.count() == users_before
    assert not any(tmp_path.rglob("*.pdf"))


# ------------------------------------------------------------------ #
# E-mail + mot de passe, mot de passe oublié, Google / Apple          #
# ------------------------------------------------------------------ #

import re  # noqa: E402

from django.core import mail  # noqa: E402

from apps.accounts import social  # noqa: E402
from apps.accounts.models import SocialAccount  # noqa: E402

PASSWORD = "Lubumbashi2026"


def register_with_email(api_client, email="marie@example.com", phone="+243812300001", role="client"):
    return api_client.post(
        reverse("accounts-register"),
        {"phone": phone, "role": role, "email": email, "password": PASSWORD},
        format="json",
    )


def confirm_last_email(api_client):
    """Ouvre le lien de confirmation du dernier e-mail envoyé."""
    token = re.search(r"token=(\S+)", mail.outbox[-1].body).group(1)
    return api_client.post(reverse("accounts-email-confirm"), {"token": token}, format="json")


def register_verified(api_client, **kwargs):
    response = register_with_email(api_client, **kwargs)
    assert confirm_last_email(api_client).status_code == 200
    return response


@pytest.mark.django_db
class TestEmailPassword:
    def test_inscription_avec_email_connecte_directement(self, api_client):
        response = register_with_email(api_client, email="Marie@Example.com")
        assert response.status_code == 201
        assert response.data["tokens"]["access"]
        assert response.data["user"]["email"] == "marie@example.com"
        assert response.data["user"]["has_password"] is True
        # Le numéro n'est pas confirmé par SMS dans ce cas
        assert response.data["user"]["phone_verified"] is False

    def test_email_sans_mot_de_passe_refuse(self, api_client):
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812300001", "role": "client", "email": "a@example.com"},
            format="json",
        )
        assert response.status_code == 400

    def test_mot_de_passe_trop_faible(self, api_client):
        response = api_client.post(
            reverse("accounts-register"),
            {"phone": "+243812300001", "role": "client", "email": "a@example.com", "password": "1234"},
            format="json",
        )
        assert response.status_code == 400

    def test_email_deja_verifie_par_un_autre(self, api_client):
        register_verified(api_client)
        response = register_with_email(api_client, email="MARIE@example.com", phone="+243812300002")
        assert response.status_code == 400
        assert "email" in response.data

    def test_email_non_verifie_ne_bloque_pas_son_vrai_titulaire(self, api_client):
        """Quelqu'un a saisi l'adresse de Marie sans la confirmer : Marie peut quand même l'utiliser."""
        register_with_email(api_client, email="marie@example.com", phone="+243812300009")
        response = register_with_email(api_client, email="marie@example.com", phone="+243812300002")
        assert response.status_code == 201
        assert User.objects.get(phone="+243812300009").email is None
        assert User.objects.get(phone="+243812300002").email == "marie@example.com"

    def test_connexion_email(self, api_client):
        register_with_email(api_client)
        response = api_client.post(
            reverse("accounts-login"), {"email": "marie@example.com", "password": PASSWORD}, format="json"
        )
        assert response.status_code == 200
        assert response.data["tokens"]["access"]

    def test_mauvais_mot_de_passe_meme_message_que_email_inconnu(self, api_client):
        register_with_email(api_client)
        wrong = api_client.post(
            reverse("accounts-login"), {"email": "marie@example.com", "password": "faux-mot"}, format="json"
        )
        unknown = api_client.post(
            reverse("accounts-login"), {"email": "personne@example.com", "password": "faux-mot"}, format="json"
        )
        assert wrong.status_code == unknown.status_code == 400
        assert wrong.data == unknown.data

    def test_compte_suspendu_ne_peut_pas_se_connecter(self, api_client):
        register_with_email(api_client)
        User.objects.filter(email="marie@example.com").update(is_active=False)
        response = api_client.post(
            reverse("accounts-login"), {"email": "marie@example.com", "password": PASSWORD}, format="json"
        )
        assert response.status_code == 400

    def test_compte_telephone_sans_mot_de_passe_ne_se_connecte_pas_par_email(self, api_client):
        User.objects.create_user(phone="+243812300003", role="client", email="tel@example.com")
        response = api_client.post(
            reverse("accounts-login"), {"email": "tel@example.com", "password": ""}, format="json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestForgotPassword:
    def test_parcours_complet(self, api_client):
        register_verified(api_client)
        mail.outbox.clear()
        response = api_client.post(
            reverse("accounts-password-forgot"), {"email": "marie@example.com"}, format="json"
        )
        assert response.status_code == 200
        assert len(mail.outbox) == 1
        link = re.search(r"uid=([^&\s]+)&token=(\S+)", mail.outbox[0].body)
        uid, token = link.groups()
        response = api_client.post(
            reverse("accounts-password-reset"),
            {"uid": uid, "token": token, "password": "NouveauSecret42"},
            format="json",
        )
        assert response.status_code == 200
        login = api_client.post(
            reverse("accounts-login"), {"email": "marie@example.com", "password": "NouveauSecret42"}, format="json"
        )
        assert login.status_code == 200
        # Le lien ne sert qu'une fois
        again = api_client.post(
            reverse("accounts-password-reset"),
            {"uid": uid, "token": token, "password": "EncoreAutre77"},
            format="json",
        )
        assert again.status_code == 400

    def test_adresse_inconnue_meme_reponse_sans_email(self, api_client):
        response = api_client.post(
            reverse("accounts-password-forgot"), {"email": "inconnu@example.com"}, format="json"
        )
        assert response.status_code == 200
        assert mail.outbox == []

    def test_lien_invalide(self, api_client):
        response = api_client.post(
            reverse("accounts-password-reset"),
            {"uid": "abc", "token": "faux", "password": "NouveauSecret42"},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestSecuritySettings:
    def test_compte_telephone_ajoute_email_et_mot_de_passe(self, authenticated_client):
        response = authenticated_client.post(
            reverse("accounts-password-change"), {"new_password": PASSWORD}, format="json"
        )
        assert response.status_code == 200
        # Les anciens jetons sont révoqués : on continue avec les nouveaux
        authenticated_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['tokens']['access']}")
        # Ensuite, le mot de passe actuel est demandé pour changer l'e-mail
        response = authenticated_client.post(
            reverse("accounts-email"), {"email": "nouveau@example.com"}, format="json"
        )
        assert response.status_code == 400
        response = authenticated_client.post(
            reverse("accounts-email"),
            {"email": "nouveau@example.com", "current_password": PASSWORD},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["user"]["email"] == "nouveau@example.com"

    def test_changer_mot_de_passe_demande_l_actuel(self, api_client):
        token = register_with_email(api_client).data["tokens"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.post(
            reverse("accounts-password-change"),
            {"current_password": "mauvais", "new_password": "NouveauSecret42"},
            format="json",
        )
        assert response.status_code == 400

    def test_options_de_connexion(self, api_client, settings):
        settings.GOOGLE_CLIENT_ID = "google-id"
        settings.APPLE_CLIENT_ID = ""
        response = api_client.get(reverse("accounts-auth-options"))
        assert response.data == {"sms": True, "google_client_id": "google-id", "apple_client_id": ""}


@pytest.fixture
def google(settings, monkeypatch):
    """Google configuré ; le jeton « bon-jeton » est accepté (sans appel à Google)."""
    settings.GOOGLE_CLIENT_ID = "google-id"
    identity = {"value": social.SocialIdentity(uid="g-123", email="marie@gmail.com")}

    def fake_verify(provider, token):
        if token != "bon-jeton":
            raise social.SocialAuthError("signature")
        return identity["value"]

    monkeypatch.setattr(social, "verify_id_token", fake_verify)
    return identity


def social_login(api_client, **extra):
    return api_client.post(
        reverse("accounts-social"), {"provider": "google", "id_token": "bon-jeton", **extra}, format="json"
    )


@pytest.mark.django_db
class TestSocialLogin:
    def test_non_configure(self, api_client):
        response = social_login(api_client)
        assert response.status_code == 503

    def test_jeton_refuse(self, api_client, google):
        response = social_login(api_client, id_token="faux")
        assert response.status_code == 400
        assert "registration_required" not in response.data

    def test_nouveau_compte_en_deux_temps(self, api_client, google):
        first = social_login(api_client)
        assert first.status_code == 400
        assert first.data["registration_required"] is True
        assert first.data["email"] == "marie@gmail.com"
        second = social_login(api_client, role="travailleur", phone="+243812300004")
        assert second.status_code == 201
        user = User.objects.get(phone="+243812300004")
        assert user.email == "marie@gmail.com"
        assert user.role == "travailleur"
        assert not user.has_usable_password()
        # Les fois suivantes : connexion directe
        third = social_login(api_client)
        assert third.status_code == 200
        assert third.data["user"]["social_providers"] == ["google"]

    def test_meme_email_verifie_relie_au_compte_existant(self, api_client, google):
        register_verified(api_client, email="marie@gmail.com")
        response = social_login(api_client)
        assert response.status_code == 200
        assert SocialAccount.objects.filter(uid="g-123", user__email="marie@gmail.com").exists()

    def test_email_non_verifie_ne_relie_pas(self, api_client, google):
        register_with_email(api_client, email="marie@gmail.com")
        google["value"] = social.SocialIdentity(uid="g-999", email=None)
        response = social_login(api_client)
        assert response.status_code == 400
        assert response.data["registration_required"] is True

    def test_numero_deja_utilise(self, api_client, google, registered_user):
        response = social_login(api_client, role="client", phone="+243812345678")
        assert response.status_code == 400
        assert "phone" in response.data

    def test_compte_suspendu(self, api_client, google):
        social_login(api_client, role="client", phone="+243812300005")
        User.objects.filter(phone="+243812300005").update(is_active=False)
        response = social_login(api_client)
        assert response.status_code == 400


class TestVerifyIdToken:
    """Vérification réelle de la signature (avec une clé de test générée sur place)."""

    @pytest.fixture
    def signer(self, settings, monkeypatch):
        import time

        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa

        settings.GOOGLE_CLIENT_ID = "google-id"
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        class FakeJWKS:
            def get_signing_key_from_jwt(self, token):
                return type("Key", (), {"key": private.public_key()})()

        monkeypatch.setitem(social._jwks_clients, "google", FakeJWKS())

        def sign(**overrides):
            claims = {
                "iss": "https://accounts.google.com",
                "aud": "google-id",
                "sub": "g-1",
                "email": "a@gmail.com",
                "email_verified": True,
                "exp": int(time.time()) + 600,
                **overrides,
            }
            return jwt.encode(claims, private, algorithm="RS256")

        return sign

    def test_jeton_valide(self, signer):
        identity = social.verify_id_token("google", signer())
        assert identity == social.SocialIdentity(uid="g-1", email="a@gmail.com")

    def test_email_non_verifie_ignore(self, signer):
        assert social.verify_id_token("google", signer(email_verified=False)).email is None

    @pytest.mark.parametrize(
        "overrides", [{"aud": "autre-application"}, {"iss": "https://pirate.example"}, {"exp": 1}]
    )
    def test_jeton_refuse(self, signer, overrides):
        with pytest.raises(social.SocialAuthError):
            social.verify_id_token("google", signer(**overrides))


# ------------------------------------------------------------------ #
# Photo de profil                                                      #
# ------------------------------------------------------------------ #

from io import BytesIO  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from PIL import Image  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

from apps.accounts import photos  # noqa: E402
from apps.notifications.models import Notification  # noqa: E402


def image_file(fmt="JPEG", size=(1600, 1200), name="moi.jpg", exif_gps=False):
    buffer = BytesIO()
    image = Image.new("RGB", size, "purple")
    kwargs = {}
    if exif_gps:
        exif = Image.Exif()
        exif[0x8825] = {1: "S", 2: (11.0, 40.0, 0.0)}  # position GPS (Lubumbashi)
        kwargs["exif"] = exif
    image.save(buffer, format=fmt, **kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


@pytest.fixture
def photo_user(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(phone="+243812300010", role=User.ROLE_WORKER)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return user, client


@pytest.mark.django_db
class TestPhoto:
    def test_envoi_reduit_et_nettoie_la_photo(self, photo_user):
        user, client = photo_user
        response = client.post(reverse("accounts-photo"), {"photo": image_file(exif_gps=True)}, format="multipart")
        assert response.status_code == 200
        assert response.data["user"]["photo_status"] == "en_attente"
        user.refresh_from_db()
        stored = Image.open(user.photo.open("rb"))
        assert stored.format == "JPEG"
        assert max(stored.size) == photos.MAX_SIDE_PX
        assert 0x8825 not in stored.getexif()  # plus de position GPS

    def test_photo_en_attente_invisible_pour_les_autres(self, photo_user):
        user, client = photo_user
        client.post(reverse("accounts-photo"), {"photo": image_file()}, format="multipart")
        user.refresh_from_db()
        name = user.photo.name.rsplit("/", 1)[-1]
        assert photos.public_photo_url(user) is None
        assert APIClient().get(reverse("public-photo", args=[name])).status_code == 404
        # La personne elle-même la voit
        assert client.get(reverse("accounts-photo")).status_code == 200

    def test_photo_validee_visible_par_tous(self, photo_user):
        user, client = photo_user
        client.post(reverse("accounts-photo"), {"photo": image_file(fmt="PNG", name="moi.png")}, format="multipart")
        user.refresh_from_db()
        photos.review_photo(user, approved=True)
        url = photos.public_photo_url(user)
        assert url.startswith("/api/photos/")
        response = APIClient().get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "image/jpeg"
        assert Notification.objects.get(user=user).params["approved"] is True

    def test_photo_refusee_supprimee_avec_motif(self, photo_user):
        user, client = photo_user
        client.post(reverse("accounts-photo"), {"photo": image_file()}, format="multipart")
        user.refresh_from_db()
        path = user.photo.path
        photos.review_photo(user, approved=False, reason="Visage non visible.")
        user.refresh_from_db()
        assert user.photo_status == "rejetee"
        assert not user.photo
        import os

        assert not os.path.exists(path)
        assert client.get(reverse("accounts-me")).data["photo_rejection_reason"] == "Visage non visible."

    def test_nouvelle_photo_repasse_en_attente(self, photo_user):
        user, client = photo_user
        client.post(reverse("accounts-photo"), {"photo": image_file()}, format="multipart")
        user.refresh_from_db()
        photos.review_photo(user, approved=True)
        client.post(reverse("accounts-photo"), {"photo": image_file()}, format="multipart")
        user.refresh_from_db()
        assert user.photo_status == "en_attente"
        assert photos.public_photo_url(user) is None

    def test_fichier_qui_n_est_pas_une_image(self, photo_user):
        _, client = photo_user
        fake = SimpleUploadedFile("virus.jpg", b"pas une image", content_type="image/jpeg")
        response = client.post(reverse("accounts-photo"), {"photo": fake}, format="multipart")
        assert response.status_code == 400

    def test_supprimer_sa_photo(self, photo_user):
        user, client = photo_user
        client.post(reverse("accounts-photo"), {"photo": image_file()}, format="multipart")
        assert client.delete(reverse("accounts-photo")).status_code == 200
        user.refresh_from_db()
        assert user.photo_status == "aucune" and not user.photo


# ------------------------------------------------------------------ #
# Sessions révocables (déconnexion, changement de mot de passe)       #
# ------------------------------------------------------------------ #


def tokens_for(user):
    from common.authentication import tokens_for as make_tokens

    refresh = make_tokens(user)
    return str(refresh.access_token), str(refresh)


def as_bearer(access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def refresh_status(refresh):
    return APIClient().post(reverse("token-refresh"), {"refresh": refresh}, format="json")


@pytest.mark.django_db
class TestSessions:
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            phone="+243812300020", role="client", email="s@example.com", password=PASSWORD, email_verified=True
        )

    def test_refresh_ne_sert_qu_une_fois(self, user):
        _, refresh = tokens_for(user)
        first = refresh_status(refresh)
        assert first.status_code == 200 and first.data["refresh"] != refresh
        assert refresh_status(refresh).status_code == 401  # réutilisation refusée

    def test_deconnexion_revoque_le_refresh(self, user):
        _, refresh = tokens_for(user)
        assert APIClient().post(reverse("accounts-logout"), {"refresh": refresh}, format="json").status_code == 200
        assert refresh_status(refresh).status_code == 401
        # Jeton inconnu ou déjà révoqué : réponse identique
        assert APIClient().post(reverse("accounts-logout"), {"refresh": "nimporte"}, format="json").status_code == 200

    def test_changement_de_mot_de_passe_deconnecte_les_autres_appareils(self, user):
        other_access, other_refresh = tokens_for(user)
        mine = as_bearer(tokens_for(user)[0])
        response = mine.post(
            reverse("accounts-password-change"),
            {"current_password": PASSWORD, "new_password": "AutreSecret99"},
            format="json",
        )
        assert response.status_code == 200
        assert as_bearer(other_access).get(reverse("accounts-me")).status_code == 401
        assert refresh_status(other_refresh).status_code == 401
        # L'appareil qui a changé le mot de passe continue avec ses nouveaux jetons
        assert as_bearer(response.data["tokens"]["access"]).get(reverse("accounts-me")).status_code == 200

    def test_reinitialisation_deconnecte_partout(self, user):
        access, refresh = tokens_for(user)
        api = APIClient()
        api.post(reverse("accounts-password-forgot"), {"email": "s@example.com"}, format="json")
        uid, token = re.search(r"uid=([^&\s]+)&token=(\S+)", mail.outbox[0].body).groups()
        api.post(reverse("accounts-password-reset"), {"uid": uid, "token": token, "password": "NouveauSecret42"}, format="json")
        assert as_bearer(access).get(reverse("accounts-me")).status_code == 401
        assert refresh_status(refresh).status_code == 401

    def test_deconnexion_de_tous_les_appareils(self, user):
        access, refresh = tokens_for(user)
        assert as_bearer(access).post(reverse("accounts-logout-all")).status_code == 200
        assert as_bearer(access).get(reverse("accounts-me")).status_code == 401
        assert refresh_status(refresh).status_code == 401

    def test_compte_suspendu_ne_peut_plus_renouveler(self, user):
        _, refresh = tokens_for(user)
        user.is_active = False
        user.save()
        assert refresh_status(refresh).status_code == 401



# ------------------------------------------------------------------ #
# Vérification de l'adresse e-mail                                     #
# ------------------------------------------------------------------ #


@pytest.mark.django_db
class TestEmailVerification:
    def test_lien_envoye_puis_confirme(self, api_client):
        response = register_with_email(api_client)
        assert response.data["user"]["email_verified"] is False
        assert "confirmer" in mail.outbox[-1].body
        assert confirm_last_email(api_client).status_code == 200
        assert User.objects.get(email="marie@example.com").email_verified is True

    def test_lien_falsifie_ou_ancien(self, api_client):
        register_with_email(api_client)
        assert api_client.post(reverse("accounts-email-confirm"), {"token": "faux"}, format="json").status_code == 400
        # L'adresse a changé depuis l'envoi : l'ancien lien ne confirme pas la nouvelle
        old_body = mail.outbox[-1].body
        user = User.objects.get(email="marie@example.com")
        user.email = "autre@example.com"
        user.save()
        token = re.search(r"token=(\S+)", old_body).group(1)
        assert api_client.post(reverse("accounts-email-confirm"), {"token": token}, format="json").status_code == 400
        user.refresh_from_db()
        assert user.email_verified is False

    def test_mot_de_passe_oublie_ignore_une_adresse_non_verifiee(self, api_client):
        register_with_email(api_client)
        mail.outbox.clear()
        response = api_client.post(reverse("accounts-password-forgot"), {"email": "marie@example.com"}, format="json")
        assert response.status_code == 200  # même réponse…
        assert mail.outbox == []  # …mais aucun lien envoyé

    def test_changer_d_adresse_demande_une_nouvelle_confirmation(self, api_client):
        token = register_verified(api_client).data["tokens"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.post(
            reverse("accounts-email"), {"email": "nouvelle@example.com", "current_password": PASSWORD}, format="json"
        )
        assert response.data["user"]["email_verified"] is False
        assert mail.outbox[-1].to == ["nouvelle@example.com"]

    def test_renvoyer_le_lien(self, api_client):
        token = register_with_email(api_client).data["tokens"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        mail.outbox.clear()
        assert api_client.post(reverse("accounts-email-resend")).status_code == 200
        assert len(mail.outbox) == 1
        confirm_last_email(api_client)
        assert api_client.post(reverse("accounts-email-resend")).status_code == 400  # déjà confirmée

    def test_google_recupere_une_adresse_seulement_saisie_par_un_autre(self, api_client, google):
        """Prise de contrôle empêchée : l'adresse non vérifiée d'un autre compte ne le relie pas."""
        register_with_email(api_client, email="marie@gmail.com", phone="+243812300009")
        first = social_login(api_client)
        assert first.status_code == 400 and first.data["registration_required"] is True
        created = social_login(api_client, role="client", phone="+243812300002")
        assert created.status_code == 201
        assert created.data["user"]["email"] == "marie@gmail.com"
        assert created.data["user"]["email_verified"] is True
        assert User.objects.get(phone="+243812300009").email is None


@pytest.mark.django_db
def test_image_geante_refusee(photo_user):
    """Une image piégée (énorme une fois décompressée) est refusée sans être décompressée."""
    _, client = photo_user
    buffer = BytesIO()
    Image.new("1", (8000, 8000)).save(buffer, format="PNG")  # 64 millions de pixels, fichier minuscule
    huge = SimpleUploadedFile("piege.png", buffer.getvalue(), content_type="image/png")
    assert client.post(reverse("accounts-photo"), {"photo": huge}, format="multipart").status_code == 400



@pytest.mark.django_db
def test_session_expire_apres_30_minutes_d_inactivite(settings):
    """Le refresh expire 30 min après sa dernière utilisation (fenêtre glissante)."""
    from datetime import timedelta

    from rest_framework_simplejwt.settings import api_settings

    assert api_settings.REFRESH_TOKEN_LIFETIME == timedelta(minutes=30)
    assert api_settings.ACCESS_TOKEN_LIFETIME < api_settings.REFRESH_TOKEN_LIFETIME
    user = User.objects.create_user(phone="+243812300030", role="client")
    _, refresh = tokens_for(user)
    renewed = refresh_status(refresh)
    assert renewed.status_code == 200  # utilisé à temps : nouveau refresh, nouvelle fenêtre
    from common.authentication import tokens_for as make_tokens

    stale = make_tokens(user)
    stale.set_exp(lifetime=-timedelta(seconds=1))  # 30 min écoulées sans activité
    assert refresh_status(str(stale)).status_code == 401
