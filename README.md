# NOUNOU+ — Backend API

Marketplace de mise en relation entre familles et travailleurs domestiques à Lubumbashi, RDC.

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

## Interface d'administration

```bash
# Créer un compte administrateur (une seule fois)
python manage.py createsuperuser
```

Puis ouvrir **http://127.0.0.1:8000/admin/**. C'est là que l'administrateur valide
les profils travailleurs (action « Marquer comme vérifié »). Seuls les profils
vérifiés apparaissent dans `/api/workers/`.

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
│   └── workers/       → Profils travailleurs ✅
├── common/            → Utilitaires partagés (à venir)
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
