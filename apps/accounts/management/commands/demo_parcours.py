"""
Commande de démonstration : joue automatiquement tout le parcours NOUNOU+.

    python manage.py demo_parcours            → montre le parcours puis efface tout
    python manage.py demo_parcours --garder   → garde les données de démo dans la base
                                                (pour les explorer ensuite dans /admin/)

Chaque étape appelle la vraie API (exactement comme le fera l'application mobile)
et affiche le résultat en français. Utile pour vérifier en une commande que tout
fonctionne sur votre ordinateur.
"""
import time
from datetime import timedelta

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.matching.models import Match
from apps.reports.models import Report
from apps.verification.models import VerificationRecord


class _Rollback(Exception):
    """Sert à annuler toutes les données de démo à la fin."""


class Command(BaseCommand):
    help = "Joue automatiquement tout le parcours NOUNOU+ (inscription → avis → signalement)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--garder",
            action="store_true",
            help="Garder les données de démo dans la base au lieu de les effacer.",
        )

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------

    def step(self, number, title):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"Étape {number} — {title}"))

    def ok(self, text):
        self.stdout.write(self.style.SUCCESS(f"  ✔ {text}"))

    def info(self, text):
        self.stdout.write(f"    {text}")

    @staticmethod
    def _host():
        """Un nom d'hôte autorisé par ALLOWED_HOSTS (les requêtes restent internes)."""
        hosts = [h for h in settings.ALLOWED_HOSTS if h and "*" not in h and not h.startswith(".")]
        return hosts[0] if hosts else "localhost"

    def call(self, method, url, token=None, data=None, fmt="json", expected=(200, 201)):
        """Appelle l'API ; arrête la démo avec un message clair si la réponse est inattendue."""
        client = APIClient(SERVER_NAME=self._host())
        if token:
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = getattr(client, method)(url, data, format=fmt)
        if response.status_code not in expected:
            detail = getattr(response, "data", None) or response.content[:300]
            raise CommandError(f"{method.upper()} {url} a répondu {response.status_code} : {detail}")
        return response

    # ------------------------------------------------------------------
    # Parcours
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        if not settings.OTP_MOCK_ENABLED:
            raise CommandError("La démo nécessite l'OTP simulé (paramètres de développement).")

        self.stored_files = []
        keep = options["garder"]
        try:
            with transaction.atomic():
                self.run_demo()
                if not keep:
                    raise _Rollback()
        except _Rollback:
            # Les données ont été annulées ; on efface aussi le document envoyé
            for storage, name in self.stored_files:
                storage.delete(name)
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(
                "Démo terminée avec succès. Les données de démo ont été effacées "
                "(relancez avec --garder pour les conserver)."
            ))
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Démo terminée avec succès. Les données sont conservées : ouvrez /admin/ pour les voir "
            f"(numéros {self.client_phone} et {self.worker_phone})."
        ))

    def run_demo(self):
        suffix = str(int(time.time()))[-6:]
        self.client_phone = f"+243810{suffix}"
        self.worker_phone = f"+243820{suffix}"

        # 1. Inscription et connexion
        self.step(1, "Inscription et connexion par code SMS (simulé : 123456)")
        tokens = {}
        for phone, role, label in [
            (self.client_phone, "client", "Famille"),
            (self.worker_phone, "travailleur", "Travailleuse"),
        ]:
            self.call("post", "/api/accounts/register/", data={"phone": phone, "role": role})
            response = self.call(
                "post", "/api/accounts/otp/verify/", data={"phone": phone, "code": "123456"}
            )
            tokens[role] = response.data["tokens"]["access"]
            self.ok(f"{label} inscrite et connectée ({phone})")
        tc, tw = tokens["client"], tokens["travailleur"]

        # 2. Profils
        self.step(2, "Création des profils")
        self.call("post", "/api/clients/profile/", tc, {
            "first_name": "Sarah", "last_name": "Kasongo", "location": "Golf",
            "services_needed": "nounou", "availability_needed": "temps_plein", "budget": "300000",
        })
        self.ok("Profil famille : Sarah Kasongo, quartier Golf")
        response = self.call("post", "/api/workers/profile/", tw, {
            "first_name": "Grace", "last_name": "Mutombo", "services": "nounou,cuisine",
            "years_experience": 5, "availability": "temps_plein",
            "expected_salary": "250000", "location": "Kenya",
        })
        worker_id = response.data["profile"]["id"]
        self.ok("Profil travailleuse : Grace Mutombo, nounou et cuisine, 5 ans d'expérience")

        # 3. Vérification
        self.step(3, "Vérification de la pièce d'identité")
        document = SimpleUploadedFile("carte.pdf", b"%PDF-1.4 demo", content_type="application/pdf")
        self.call("post", "/api/verification/documents/", tw,
                  {"doc_type": "identite", "file": document}, fmt="multipart")
        self.ok("La travailleuse envoie sa pièce d'identité")
        record = VerificationRecord.objects.get(worker_id=worker_id)
        self.stored_files.append((record.file.storage, record.file.name))
        admin = User.objects.filter(is_superuser=True).first()
        record.review(admin, VerificationRecord.STATUS_APPROVED)
        response = self.call("get", "/api/verification/documents/", tw)
        self.ok(f"L'administrateur valide le document → badge vérifié : {response.data['is_verified']}")

        # 4. Annonce
        self.step(4, "La famille publie une annonce")
        response = self.call("post", "/api/jobs/", tc, {
            "title": "Nounou pour 2 enfants", "service": "nounou",
            "availability": "temps_plein", "budget": "300000",
            "description": "Du lundi au vendredi, 7h-17h.",
        })
        job_id = response.data["job"]["id"]
        self.ok("Annonce publiée : « Nounou pour 2 enfants », 300 000 FC / mois")

        # 5. Recherche
        self.step(5, "Recherche")
        response = self.call("get", "/api/jobs/?service=nounou&location=golf", tw)
        job = next(j for j in response.data["results"] if j["id"] == job_id)
        self.ok(f"La travailleuse trouve l'annonce, publiée par « {job['client']['name']} »")
        self.info("(nom de famille masqué et pas de téléphone avant le match)")
        response = self.call("get", "/api/workers/?service=nounou&max_salary=300000", tc)
        found = next(w for w in response.data["results"] if w["id"] == worker_id)
        self.ok(f"La famille trouve « {found['first_name']} {found['last_name']} » "
                f"(téléphone affiché : {found['phone_display']})")

        # 6. Mise en relation
        self.step(6, "Mise en relation")
        response = self.call("post", f"/api/jobs/{job_id}/interest/", tw)
        match_id = response.data["match"]["id"]
        self.ok("La travailleuse répond à l'annonce")
        response = self.call("post", "/api/matches/interest/", tc, {"profile_id": worker_id})
        other = response.data["match"]["other_party"]
        self.ok(f"La famille accepte → {response.data['message']}")
        self.info(f"Coordonnées révélées : {other['first_name']} {other['last_name']}, {other['phone']}")

        # 7. Messagerie
        self.step(7, "Messagerie")
        self.call("post", f"/api/matches/{match_id}/messages/", tc,
                  {"content": "Bonjour Grace, pouvez-vous commencer lundi ?"})
        self.ok("La famille envoie un message")
        response = self.call("get", "/api/matches/", tw)
        unread = next(m for m in response.data["results"] if m["id"] == match_id)["unread_count"]
        self.ok(f"La travailleuse a {unread} message non lu")
        self.call("post", f"/api/matches/{match_id}/messages/", tw,
                  {"content": "Bonjour Sarah, oui avec plaisir !"})
        response = self.call("get", f"/api/matches/{match_id}/messages/", tc)
        self.ok(f"Conversation : {len(response.data['results'])} messages échangés")

        # 8. Évaluations
        self.step(8, "Évaluations après la période d'essai")
        Match.objects.filter(pk=match_id).update(first_mutual_at=timezone.now() - timedelta(days=8))
        self.info("(pour la démo, on fait comme si le match datait d'il y a 8 jours)")
        self.call("post", f"/api/matches/{match_id}/review/", tc, {
            "punctuality": 5, "competence": 5, "reliability": 4, "comment": "Très sérieuse.",
        })
        self.ok("La famille note la travailleuse")
        self.call("post", f"/api/matches/{match_id}/review/", tw, {
            "respect": 5, "clarity": 4, "payment_on_time": 5,
        })
        self.ok("La travailleuse note la famille")
        response = self.call("get", f"/api/reviews/workers/{worker_id}/", tc)
        rating = response.data["summary"]
        self.ok(f"Note de la travailleuse : {rating['average']}/5 ({rating['count']} avis)")

        # 9. Signalement
        self.step(9, "Signalement et décision de l'administrateur")
        client_profile_id = User.objects.get(phone=self.client_phone).client_profile.id
        self.call("post", "/api/reports/", tw, {
            "profile_id": client_profile_id, "category": "comportement_inapproprie",
            "description": "Exemple de signalement pour la démo.",
        })
        self.ok("La travailleuse signale un comportement (anonymement)")
        Report.objects.filter(reporter__phone=self.worker_phone).get().decide(
            admin, Report.STATUS_WARNED, "Merci de rester courtois dans vos échanges."
        )
        response = self.call("get", "/api/accounts/me/", tc)
        self.ok(f"L'administrateur envoie un avertissement → la famille voit : "
                f"« {response.data['warnings'][0]['message']} »")
        self.info("(sans jamais savoir qui l'a signalée)")
