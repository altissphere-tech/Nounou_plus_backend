# NOUNOU+ — Brief technique backend (V1 / MVP)

## Contexte
NOUNOU+ est une marketplace bidirectionnelle mettant en relation des familles (clients) et des travailleurs domestiques (nounous, femmes de ménage, cuisinières) à Lubumbashi, RDC. Ce brief couvre uniquement le **backend V1 (MVP)**. Le fondateur (Light) n'est pas développeur — il pilote le projet en langage naturel via un agent IA. Toute décision technique doit être expliquée simplement avant d'être appliquée.

## Stack retenue pour le développement local (pas de Docker pour l'instant)
- **Langage/Framework** : Python 3.12 + Django + Django REST Framework
- **Base de données (dev)** : SQLite (fichier local, aucune installation requise)
- **Base de données (prod, plus tard)** : PostgreSQL — à anticiper dans les modèles (éviter les fonctionnalités spécifiques à SQLite)
- **Redis / Celery** : PAS utilisés en V1 (tâches asynchrones reportées à V2)
- **Authentification** : JWT (via `djangorestframework-simplejwt`) + vérification par OTP téléphone (mock/simulé en V1, vrai SMS en V2)
- **Stockage fichiers (photos, documents)** : stockage local sur disque en dev ; prévoir une interface facilement remplaçable par S3-compatible plus tard
- **Tests** : `pytest` + `pytest-django`, un test minimum par endpoint critique

## Structure de projet attendue

```
nounou-backend/
├── config/
│   ├── settings/ (base.py, dev.py, prod.py, test.py)
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/       # comptes, rôles (client/travailleur/admin), OTP
│   ├── workers/        # profils travailleurs
│   ├── clients/        # profils clients
│   ├── services/       # catalogue de services (nounou, ménage, cuisine)
│   ├── jobs/            # demandes / offres
│   ├── messaging/       # messagerie interne post-match
│   ├── verification/    # documents et statut de vérification
│   ├── reviews/         # évaluations bidirectionnelles
│   ├── reports/         # signalements
│   └── administration/  # back-office simple
├── common/               # permissions, pagination, exceptions partagées
├── requirements/
│   ├── base.txt
│   └── dev.txt
├── .env.example
├── manage.py
└── README.md
```

**Règle stricte** : chaque app Django a son propre `models.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py`. Jamais de fichier monolithique.

## Périmètre fonctionnel V1 (ne pas dépasser)

| Module | Client | Travailleur | Admin |
|---|---|---|---|
| Compte | Inscription, profil | Inscription, profil pro | — |
| Recherche | Recherche + filtres simples (service, localisation, budget) | Consultation des offres | — |
| Confiance | Voir badge "vérifié" | Soumission de documents | Validation manuelle des profils |
| Mise en relation | Intérêt + match mutuel | Intérêt + match mutuel | — |
| Communication | Messagerie interne | Messagerie interne | Modération basique |
| Évaluation | Note post-essai | Note post-essai | Vue globale |
| Signalement | Signaler un profil | Signaler un profil | Traiter les signalements |

**Explicitement HORS V1** : moteur de matching pondéré (une liste triée simplement suffit), planification d'entretien intégrée, génération automatique de contrat, paiement Mobile Money, notifications push/SMS.

## Entités principales (modèle de données)

- **User** : téléphone, rôle (client/travailleur/admin), statut OTP
- **WorkerProfile** : lié à User, services[], expérience, disponibilité, prétention salariale, localisation, statut de vérification
- **ClientProfile** : lié à User, localisation, besoins
- **VerificationRecord** : profil concerné, type (identité/référence), statut, preuve, validé par (admin)
- **JobRequest** : client, service demandé, budget, disponibilité requise, statut
- **Match** : client, travailleur, statut (intérêt simple / mutuel / refusé)
- **Message** : match concerné, expéditeur, contenu, date
- **Review** : auteur, cible, critères notés, commentaire
- **Report** : auteur, cible, catégorie, description, statut, décision admin

## Contraintes non négociables

1. **Aucun secret dans le code** — tout passe par des variables d'environnement (`.env`, jamais commité)
2. **Coordonnées personnelles jamais exposées avant match mutuel** — logique à mettre dans les serializers (masquer téléphone/nom complet tant que le match n'est pas mutuel)
3. Le badge "vérifié" ne doit jamais être présenté dans l'API ou la documentation comme une garantie d'absence de risque
4. Prévoir dès la V1 la possibilité d'ajouter Redis/Celery/Postgres sans réécrire l'architecture (pas de dépendance dure à SQLite dans le code métier)

## Mode de travail attendu de l'agent

Le fondateur pilote en langage naturel et ne lit pas le code ligne par ligne. En conséquence :

- Avant de lancer une étape structurante (ex. créer l'architecture, choisir une librairie), **explique en une phrase simple ce que tu vas faire et pourquoi**
- Avance par petites étapes vérifiables : une app à la fois, avec un moyen simple de tester (ex. `python manage.py runserver` + endpoint testable)
- Si une décision a un impact business ou juridique (ex. structure des données personnelles, ce qui est visible avant/après match), **demande confirmation avant d'implémenter**
- Ne pas introduire Docker, Postgres, Redis ou Celery en V1 sauf demande explicite

## Première tâche à réaliser

Initialiser le projet Django selon la structure ci-dessus, avec seulement l'app `accounts` fonctionnelle (modèle `User` personnalisé avec rôle, inscription, connexion par OTP simulé), un `README.md` expliquant comment lancer le projet, et un test qui vérifie que l'inscription fonctionne.
