# Guide d'essai NOUNOU+ (backend V1)

Ce guide permet de vérifier, sur votre ordinateur Windows, que tout le backend
fonctionne — sans écrire de code. Comptez **15 minutes** la première fois.

---

## Étape 0 — Récupérer la dernière version (une seule fois)

> ⚠️ **Avant tout**, copiez votre fichier `.env` dans un autre dossier (ex : le Bureau).
> La nouvelle version ne suit plus ce fichier dans git : il peut disparaître lors de la mise à jour.

Dans le terminal, dans le dossier du projet :

```bash
git fetch origin
git checkout claude/funny-cray-8bklxl
git pull
```

Puis :

1. **Remettez votre `.env`** dans le dossier du projet (ou copiez `.env.example` en `.env`).
2. **Changez la `SECRET_KEY`** dans `.env` (l'ancienne a été publiée sur GitHub) :
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copiez la valeur affichée après `SECRET_KEY=`.
3. **Recréez l'environnement Python** (le dossier `venv` a pu être supprimé) :
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements/dev.txt
   ```
4. **Mettez à jour la base de données** :
   ```bash
   python manage.py migrate
   ```

---

## Étape 1 — Lancer les tests automatiques (1 minute)

```bash
pytest
```

✅ Résultat attendu : une ligne verte du type **`192 passed`**.
Chaque test vérifie une règle (ex : « le téléphone est masqué avant le match »).
Si une ligne rouge `FAILED` apparaît, copiez-la et envoyez-la à votre agent IA.

---

## Étape 2 — Voir tout le parcours en une commande (1 minute)

```bash
python manage.py demo_parcours
```

La commande joue automatiquement l'histoire complète d'une famille et d'une
travailleuse, en utilisant la vraie API :

| Étape | Ce qui est vérifié |
|---|---|
| 1 | Inscription et connexion par code SMS simulé (`123456`) |
| 2 | Création du profil famille et du profil travailleuse |
| 3 | Envoi de la pièce d'identité, validation par l'admin, badge « vérifié » |
| 4 | Publication d'une annonce par la famille |
| 5 | Recherche avec filtres — nom masqué (« Sarah K. ») et téléphone caché |
| 6 | Réponse à l'annonce, puis match mutuel → coordonnées révélées |
| 7 | Messagerie et messages non lus |
| 8 | Évaluations croisées et note moyenne |
| 9 | Signalement anonyme et avertissement de l'admin |

✅ Résultat attendu : des coches vertes ✔ et le message **« Démo terminée avec succès »**.
Par défaut, la démo **efface tout** à la fin : votre base reste propre.

---

## Étape 3 — Explorer l'interface d'administration (10 minutes)

1. Créez votre compte administrateur (une seule fois) :
   ```bash
   python manage.py createsuperuser
   ```
   Entrez votre numéro au format `+243…` et un mot de passe.
2. Relancez la démo en **gardant** les données :
   ```bash
   python manage.py demo_parcours --garder
   ```
3. Démarrez le serveur :
   ```bash
   python manage.py runserver
   ```
4. Ouvrez **http://127.0.0.1:8000/admin/** et connectez-vous.

À regarder, rubrique par rubrique :

| Rubrique | Ce que vous pouvez faire |
|---|---|
| **Utilisateurs** | Voir les comptes, leur rôle, s'ils sont actifs (non suspendus) |
| **Profils travailleurs / clients** | Voir et modifier les profils |
| **Annonces** | Voir les annonces publiées et leur statut |
| **Documents de vérification** | « Ouvrir le document », puis Validé / Rejeté (avec motif) |
| **Mises en relation** | Voir qui s'intéresse à qui, y compris les refus |
| **Messages** | Rechercher un message, le retirer (modération) |
| **Évaluations** | Vue globale des notes, retrait d'un commentaire |
| **Signalements** | Classer sans suite, avertir ou **suspendre** un compte |

💡 Essai conseillé : dans **Signalements**, ouvrez celui de la démo, choisissez
« Compte suspendu » et enregistrez. Dans **Utilisateurs**, le compte de la famille
n'est plus « actif ». Remettez « Classé sans suite » : le compte est réactivé.

Pour effacer les données de démo gardées : dans **Utilisateurs**, cochez les deux
comptes de démo (numéros affichés à la fin de la commande) → action « Supprimer ».

---

## Étape 4 (facultatif) — Tester l'API à la main

L'application mobile parlera à l'API. Pour l'essayer vous-même, le plus simple est
un logiciel comme **Postman** (gratuit) ou l'extension **Thunder Client** de VS Code.
Toutes les adresses et des exemples sont dans le `README.md`, sections
« Endpoints disponibles ».

Rappel du principe :
1. `POST /api/accounts/register/` puis `POST /api/accounts/otp/verify/` (code `123456`)
   → vous recevez un **token**.
2. Ajoutez l'en-tête `Authorization: Bearer <token>` à toutes les autres requêtes.

---

## En cas de problème

| Message | Solution |
|---|---|
| `No module named 'django'` | Activez l'environnement : `venv\Scripts\activate` |
| `SECRET_KEY` introuvable | Le fichier `.env` manque : copiez `.env.example` en `.env` |
| `no such table` | Lancez `python manage.py migrate` |
| Port déjà utilisé | Un autre serveur tourne : fermez-le (Ctrl+C) ou utilisez `runserver 8001` |
