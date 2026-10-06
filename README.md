# NOUNOU+ — Backend API

Marketplace de mise en relation entre familles et travailleurs domestiques à Lubumbashi, RDC.

> 🧪 **Pour tout essayer sans écrire de code**, suivez le guide pas à pas :
> [`docs/GUIDE_ESSAI.md`](docs/GUIDE_ESSAI.md) — ou lancez directement
> `python manage.py demo_parcours` pour voir tout le parcours en une commande.

---

## Prérequis

- Python 3.12+
- pip

---

## Installation (première fois)

```bash
# 1. Créer un environnement virtuel
python -m venv venv

# 2. Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# macOS / Linux :
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements/dev.txt

# 4. Copier le fichier de configuration
copy .env.example .env
# Puis ouvrir .env et changer SECRET_KEY par une valeur aléatoire
```

---

## Lancer le serveur

```bash
# Appliquer les migrations (crée la base de données SQLite)
python manage.py migrate

# Démarrer le serveur de développement
python manage.py runserver
```

L'API est accessible sur : **http://127.0.0.1:8000/**

### 📖 Documentation interactive

Avec le serveur lancé, ouvrez **http://127.0.0.1:8000/api/docs/** : toutes les adresses
de l'API y sont décrites (données attendues, réponses, filtres, erreurs) et peuvent être
**essayées directement dans le navigateur** :

1. rubrique « Comptes » → `POST /api/accounts/otp/request/` → *Try it out* → votre numéro → *Execute* ;
2. `POST /api/accounts/otp/verify/` avec le code `123456` → copiez la valeur `access` ;
3. bouton **Authorize** en haut de la page → collez le token → toutes les adresses sont utilisables.

Variante en lecture seule : **http://127.0.0.1:8000/api/redoc/**. Description brute (OpenAPI),
utile au développeur de l'application mobile : **http://127.0.0.1:8000/api/schema/**.
En production, ces pages seront réservées aux comptes administrateurs.

---

## Endpoints disponibles (V1 — app accounts)

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/accounts/register/` | Créer un compte (client ou travailleur) |
| POST | `/api/accounts/otp/request/` | Recevoir un code OTP sur son téléphone |
| POST | `/api/accounts/otp/verify/` | Valider le code OTP et obtenir un token JWT |
| GET  | `/api/accounts/me/` | Voir son profil (token JWT requis) |

### Exemple d'utilisation

**1. Inscription**
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+243812345678", "role": "client"}'
```

**2. Demander un OTP** *(le code s'affiche dans la console du serveur en V1)*
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+243812345678"}'
```

**3. Vérifier l'OTP** *(code toujours `123456` en V1)*
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+243812345678", "code": "123456"}'
```
→ Retourne `access` et `refresh` (tokens JWT)

**4. Voir son profil**
```bash
curl http://127.0.0.1:8000/api/accounts/me/ \
  -H "Authorization: Bearer <votre_access_token>"
```

---

## Endpoints disponibles (V1 — app workers)

Tous ces endpoints nécessitent un token JWT (`Authorization: Bearer <token>`).

| Méthode | URL | Description |
|---------|-----|-------------|
| GET   | `/api/workers/` | Liste des profils travailleurs vérifiés (client ou travailleur) |
| POST  | `/api/workers/profile/` | Créer son profil (travailleur uniquement) |
| GET   | `/api/workers/profile/me/` | Voir son propre profil (travailleur uniquement) |
| PATCH | `/api/workers/profile/me/` | Modifier son propre profil (travailleur uniquement) |

Le champ `services` s'envoie sous forme de texte séparé par des virgules,
parmi `nounou`, `menage`, `cuisine` (ex : `"nounou,cuisine"`).

---

## Recherche et pagination

**Pagination** : toutes les listes sont découpées en pages de 20.
`?page=2` pour la page suivante, `?page_size=50` pour changer la taille (100 max.).
Réponse : `{"count": 57, "next": "<url>", "previous": null, "results": [...]}`.

**Rechercher des travailleurs** — `GET /api/workers/` (filtres facultatifs, combinables) :

| Paramètre | Exemple | Effet |
|---|---|---|
| `service` | `nounou` | Propose ce service (`nounou`, `menage`, `cuisine`) |
| `location` | `kenya` | Quartier contenant ce texte (majuscules ignorées) |
| `availability` | `temps_plein` | `temps_plein`, `temps_partiel` ou `weekends` |
| `max_salary` | `200` | Prétention salariale ≤ 200 |
| `min_experience` | `2` | Au moins 2 ans d'expérience |
| `ordering` | `rating` | Tri : `recent` (défaut), `salary`, `experience`, `rating` |

Exemple : `GET /api/workers/?service=nounou&location=kenya&max_salary=200&ordering=rating`

**Rechercher des besoins clients** (travailleurs) — `GET /api/clients/` :
`service`, `location`, `availability`, `min_budget` (budget ≥ valeur).

Une valeur invalide (ex : `max_salary=beaucoup`) renvoie une erreur 400 explicative.

---

## Endpoints disponibles (V1 — app clients)

Tous ces endpoints nécessitent un token JWT d'un compte **client**.

| Méthode | URL | Description |
|---------|-----|-------------|
| POST  | `/api/clients/profile/` | Créer son profil client |
| GET   | `/api/clients/profile/me/` | Voir son propre profil |
| PATCH | `/api/clients/profile/me/` | Modifier son propre profil |
| GET   | `/api/clients/` | Liste des besoins clients — **réservé aux travailleurs** (nom réduit à l'initiale, sans téléphone) |

Exemple de création :
```bash
curl -X POST http://127.0.0.1:8000/api/clients/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <votre_access_token>" \
  -d '{"first_name": "Sarah", "last_name": "Kasongo", "location": "Bel-Air",
       "services_needed": "nounou,menage", "availability_needed": "temps_partiel",
       "budget": "150"}'
```
`budget` et `needs_description` sont facultatifs. `availability_needed` vaut
`temps_plein`, `temps_partiel` ou `weekends`.

---

## Annonces (V1 — app jobs)

Une famille peut publier **plusieurs annonces**, chacune pour un service précis
(ex : une nounou à temps plein et une cuisinière le week-end).

| Méthode | URL | Qui | Description |
|---------|-----|-----|-------------|
| POST  | `/api/jobs/` | Client | Publier une annonce |
| GET   | `/api/jobs/mine/` | Client | Ses annonces (tous statuts) |
| GET   | `/api/jobs/` | Travailleur | Annonces ouvertes (filtres `service`, `location`, `availability`, `min_budget`) |
| GET   | `/api/jobs/<id>/` | Les deux | Détail (le client : ses annonces ; le travailleur : annonces ouvertes) |
| PATCH | `/api/jobs/<id>/` | Client | Modifier, ou changer le statut : `ouverte`, `pourvue`, `fermee` |
| POST  | `/api/jobs/<id>/interest/` | Travailleur vérifié | Répondre à l'annonce |

Exemple de publication :
```json
{"title": "Nounou pour 2 enfants", "service": "nounou", "availability": "temps_plein",
 "budget": "200", "description": "Du lundi au vendredi, 7h-17h."}
```
`location` est facultatif (par défaut : le quartier du profil client), `budget` aussi.

Répondre à une annonce crée la mise en relation avec la famille (champ `job` dans
`/api/matches/`) : la famille accepte ou refuse comme d'habitude, avec les mêmes règles
de confidentialité. Les travailleurs voient la famille sous la forme « Sarah K. ».
Une annonce pourvue ou fermée disparaît de la liste des travailleurs.

---

## Mise en relation (V1 — app matching)

Tous ces endpoints nécessitent un token JWT (client ou travailleur) **et** un profil créé.

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/matches/interest/` | Se déclarer intéressé par un profil : `{"profile_id": 12}` |
| GET  | `/api/matches/` | Voir ses mises en relation |
| POST | `/api/matches/<id>/decline/` | Refuser une mise en relation |

Règles :
1. Un client choisit un **profil travailleur** (vérifiés uniquement) ; un travailleur
   choisit un **profil client**. Un travailleur doit être vérifié pour contacter un client.
2. Quand les deux sont intéressés, le statut passe à `mutuel` : le nom complet et le
   téléphone de l'autre personne apparaissent dans `other_party`.
3. Un refus n'est jamais révélé à l'autre personne : pour elle, la demande reste
   `en_attente`. On peut revenir sur un refus en se déclarant de nouveau intéressé.

---

## Messagerie (V1 — app messaging)

Ouverte uniquement entre les deux participants d'un **match mutuel**.

| Méthode | URL | Description |
|---------|-----|-------------|
| GET  | `/api/matches/<id>/messages/` | Lire la conversation (marque les messages reçus comme lus) |
| POST | `/api/matches/<id>/messages/` | Envoyer un message : `{"content": "Bonjour"}` (2000 caractères max.) |

- Dans `/api/matches/`, le champ `unread_count` indique le nombre de messages non lus.
- Si l'une des parties revient sur le match, la conversation se ferme (erreur 403).
- Modération : dans `/admin/`, l'administrateur peut retirer un message ; les
  participants voient alors « Ce message a été retiré par la modération. ».

---

## Vérification des documents (V1 — app verification)

Réservé aux **travailleurs** ayant créé leur profil.

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/verification/documents/` | Envoyer un document (formulaire multipart : `doc_type` + `file`) |
| GET  | `/api/verification/documents/` | Voir ses documents, leur statut et son badge |

Exemple d'envoi :
```bash
curl -X POST http://127.0.0.1:8000/api/verification/documents/ \
  -H "Authorization: Bearer <votre_access_token>" \
  -F doc_type=identite -F file=@carte_electeur.pdf
```

- `doc_type` : `identite` (pièce d'identité) ou `reference` (lettre de référence, facultative).
- Formats acceptés : PDF, JPG, PNG — 5 Mo maximum.
- **Seul l'administrateur voit les documents** : dans `/admin/` → « Documents de
  vérification », lien « Ouvrir le document », puis statut « Validé » ou « Rejeté »
  (avec un motif que le travailleur verra).
- Le badge « vérifié » est accordé dès qu'une pièce d'identité est validée. Ce badge
  ne constitue pas une garantie d'absence de risque.
- Les fichiers sont stockés dans le dossier `media/` (jamais envoyé sur GitHub) et ne
  sont accessibles par aucune adresse publique.

---

## Évaluations (V1 — app reviews)

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/matches/<id>/review/` | Évaluer l'autre personne d'une mise en relation |
| GET  | `/api/reviews/workers/<profile_id>/` | Avis reçus par un travailleur (moyennes + commentaires) |
| GET  | `/api/reviews/clients/<profile_id>/` | Avis reçus par un client (moyennes + commentaires) |

Règles :
1. Seules deux personnes ayant eu un **match mutuel** peuvent s'évaluer, **une seule fois** chacune
   (même si l'une s'est retirée ensuite : un essai raté doit pouvoir être signalé).
2. Possible **7 jours après le premier match mutuel** (`can_review` et `review_available_at`
   dans `/api/matches/`). Le délai se règle avec `REVIEW_DELAY_DAYS`.
3. Notes de 1 à 5 + commentaire facultatif :
   - client → travailleur : `{"punctuality": 5, "competence": 4, "reliability": 5, "comment": "…"}`
   - travailleur → client : `{"respect": 5, "clarity": 4, "payment_on_time": 5, "comment": "…"}`
4. Les profils affichent `rating` : moyenne sur 5 et nombre d'avis. Les commentaires sont
   publics, l'auteur étant présenté par son prénom et l'initiale de son nom.
5. Modération : dans `/admin/`, l'administrateur peut retirer un commentaire (la note reste comptée).

---

## Signalements (V1 — app reports)

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/reports/` | Signaler un profil : `{"profile_id": 12, "category": "arnaque", "description": "…"}` |
| GET  | `/api/reports/` | Voir ses signalements (`en_attente` ou `traite`) |

- Un client signale un **profil travailleur** qu'il voit (liste ou matchs), un travailleur
  signale un **profil client**. Aucun match n'est nécessaire.
- Catégories : `faux_profil`, `comportement_inapproprie`, `arnaque`, `securite`, `autre`
  (description obligatoire pour `autre`).
- **Anonyme** : la personne signalée ne sait jamais qui l'a signalée.
- Dans `/admin/` → « Signalements », l'administrateur décide :
  - **Classé sans suite** ;
  - **Avertissement** : le message s'affiche dans `/api/accounts/me/` (champ `warnings`) ;
  - **Compte suspendu** : plus de connexion (même avec un ancien token), disparition des
    listes, des matchs et de la messagerie. Annuler la décision réactive le compte.

---

## Catalogue des services

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/api/services/` | Liste des services (sans connexion) |

---

## Interface d'administration

```bash
# Créer un compte administrateur (une seule fois)
python manage.py createsuperuser
```

Puis ouvrir **http://127.0.0.1:8000/admin/**. C'est là que l'administrateur examine
les documents envoyés par les travailleurs et accorde le badge « vérifié » (voir la
section « Vérification des documents »). Seuls les profils vérifiés apparaissent
dans `/api/workers/`.

---

## Lancer les tests

```bash
pytest -v
```

---

## Structure du projet

```
nounou-backend/
├── config/            → Configuration Django (settings, urls, wsgi)
│   └── settings/
│       ├── base.py    → Paramètres communs
│       ├── dev.py     → Développement local (SQLite)
│       ├── prod.py    → Production (PostgreSQL prêt)
│       └── test.py    → Tests automatisés
├── apps/
│   ├── accounts/      → Comptes, rôles, OTP, JWT ✅
│   ├── services/      → Catalogue des services (nounou, ménage, cuisine) ✅
│   ├── workers/       → Profils travailleurs ✅
│   ├── clients/       → Profils clients (familles) ✅
│   ├── jobs/          → Annonces des familles ✅
│   ├── matching/      → Mise en relation (intérêt, match mutuel, refus) ✅
│   ├── messaging/     → Messagerie après match mutuel + modération ✅
│   ├── verification/  → Documents (identité, référence) et badge « vérifié » ✅
│   ├── reviews/       → Évaluations après la période d'essai ✅
│   └── reports/       → Signalements, avertissements et suspensions ✅
├── common/            → Permissions, listes de choix et règles de confidentialité partagées
├── requirements/
│   ├── base.txt       → Dépendances de production
│   └── dev.txt        → Dépendances de développement
└── manage.py          → Commandes Django
```

---

## Notes importantes

- **OTP simulé en V1** : le code est toujours `123456` et s'affiche dans la console. Il n'est actif qu'en développement et en test (`OTP_MOCK_ENABLED`). En production, l'inscription et la connexion renvoient une erreur 503 tant qu'un vrai service SMS n'est pas branché.
- **Données personnelles avant match** : dans la liste `/api/workers/`, le téléphone est masqué et le nom de famille réduit à son initiale (ex : « Grace M. »). Le travailleur voit son nom complet sur son propre profil.
- **Aucun secret dans le code** : toutes les valeurs sensibles sont dans `.env` (ne jamais committer ce fichier).
- **Base de données** : SQLite en dev, PostgreSQL préparé pour la production (aucune réécriture nécessaire).
