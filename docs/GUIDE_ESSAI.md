# Guide d'essai NOUNOU+ (backend V1)

Ce guide permet de vérifier, sur votre ordinateur Windows, que tout le backend
fonctionne — sans écrire de code. Comptez **15 minutes** la première fois.

---

## Étape 0 — Récupérer la dernière version (une seule fois)

> ⚠️ La nouvelle version ne suit plus `.env`, `db.sqlite3` ni le dossier `venv` dans git :
> changer de branche **les supprime** du dossier. On les sauvegarde donc d'abord.

Dans PowerShell, dans le dossier du projet, **une commande à la fois** :

```powershell
# 1. Sortir de l'environnement Python (sinon Windows bloque la suppression de venv)
deactivate

# 2. Sauvegarder la configuration et la base de données (un dossier au-dessus)
Copy-Item .env ..\env_sauvegarde.txt
Copy-Item db.sqlite3 ..\db_sauvegarde.sqlite3

# 3. Télécharger et changer de branche (-f : remplace db.sqlite3, déjà sauvegardé)
git fetch origin
git checkout -f claude/funny-cray-8bklxl

# 4. Remettre la configuration et la base de données
Copy-Item ..\env_sauvegarde.txt .env
Copy-Item ..\db_sauvegarde.sqlite3 db.sqlite3

# 5. Recréer un environnement Python propre
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements\dev.txt

# 6. Mettre à jour la base de données
python manage.py migrate
```

Puis **changez la `SECRET_KEY`** (l'ancienne a été publiée sur GitHub) :
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
notepad .env
```
Remplacez la valeur après `SECRET_KEY=` par celle affichée, puis enregistrez.

> 💡 Si une commande `git` affiche « Connection was reset » ou « RPC failed », c'est une
> coupure réseau passagère : relancez simplement la commande.

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
| **Photos de profil** | Voir les photos envoyées ; action « Valider » ou « Refuser » (remplir d'abord « Motif du refus ») |
| **Références** | Appeler la personne, puis « Vérifiée » ou « Non confirmée » (la note reste interne) |
| **Notifications** | Consulter ce qu'une personne a reçu (lecture seule) |

💡 Essai conseillé : dans **Signalements**, ouvrez celui de la démo, choisissez
« Compte suspendu » et enregistrez. Dans **Utilisateurs**, le compte de la famille
n'est plus « actif ». Remettez « Classé sans suite » : le compte est réactivé.

Pour effacer les données de démo gardées : dans **Utilisateurs**, cochez les deux
comptes de démo (numéros affichés à la fin de la commande) → action « Supprimer ».

---

## Étape 4 — Essayer l'API dans le navigateur (10 minutes)

Serveur lancé (`python manage.py runserver`), ouvrez **http://127.0.0.1:8000/api/docs/**.
Chaque rubrique (Comptes, Travailleurs, Annonces…) liste ses adresses ; cliquez sur
l'une d'elles pour voir ce qu'elle attend et ce qu'elle renvoie.

**Se connecter dans la page** (avec un compte de la démo `--garder`, numéro affiché à la fin) :

1. Rubrique **Comptes** → `POST /api/accounts/otp/request/` → **Try it out** →
   remplacez le numéro dans le cadre par le vôtre → **Execute**.
2. `POST /api/accounts/otp/verify/` → **Try it out** → votre numéro et le code `123456`
   → **Execute** → dans la réponse, copiez la longue valeur après `"access":` (sans les guillemets).
3. Bouton vert **Authorize** en haut → collez → **Authorize** → **Close**.

Vous pouvez maintenant tout essayer. Exemple : rubrique **Travailleurs** →
`GET /api/workers/` → **Try it out** → `service` = `nounou`, `max_salary` = `200` → **Execute**.

💡 Un code SMS ne sert qu'une fois : pour vous reconnecter, refaites les étapes 1 et 2.

---

## Étape 5 — Essayer les nouveautés dans l'application (15 minutes)

Lancez Django (`python manage.py runserver`) **et** l'application (`cd frontend`, `npm install`
la première fois, puis `npm run dev`), et ouvrez **http://localhost:5173**.

1. **Inscription par e-mail** : « Créer un compte » → choisissez « E-mail » → e-mail,
   mot de passe (8 caractères minimum) et numéro fictif (ex : `0811111111`). Le **code SMS**
   est demandé d'abord (`123456` en développement) : sans lui, aucun compte n'est utilisable.
   Un lien de confirmation est ensuite envoyé : en développement, l'e-mail **s'affiche dans
   la fenêtre où tourne Django** ; copiez le lien (`http://localhost:5173/email/confirmer?token=…`)
   dans le navigateur. Tant qu'il n'est pas ouvert, l'adresse ne permet pas de se connecter.
2. **Mot de passe oublié** (adresse confirmée uniquement) : déconnectez-vous (onglet **Profil** →
   « Se déconnecter »), puis « Se connecter » → « E-mail » → « Mot de passe oublié ? ». Le lien
   s'affiche lui aussi dans la fenêtre de Django.
3. **Photo de profil** : **Profil** → « Modifier mon profil » → « Ajouter une photo ».
   Elle reste « en attente » jusqu'à votre validation dans l'admin (**Photos de profil**).
4. **Références** (compte travailleur) : **Profil** → « Vérification et références ».
5. **Favoris** : compte famille → **Rechercher** → touchez le cœur ; retrouvez-les dans **Profil** → « Mes favoris ».
6. **Notifications** : la cloche en haut à droite compte les nouveautés (intérêt reçu, match,
   messages, photo validée…).
7. **Aide**, **Conditions d'utilisation** et **Sécurité** : depuis l'onglet **Profil**.
   Dans **Sécurité** : confirmer son numéro, son e-mail, changer de mot de passe et
   « Se déconnecter de tous les appareils ».

**Travailleur non vérifié** : les annonces et les familles restent cachées (message
« visibles une fois votre profil vérifié ») jusqu'à la validation de ses documents dans l'admin.

**Limites d'essais** : en développement, elles sont plus larges qu'en production. Si vous voyez
« Requête ralentie », attendez quelques minutes (ou redémarrez Django).

**Google et Apple** : les boutons restent grisés (« bientôt disponible ») tant que les comptes
développeur ne sont pas créés. Il faudra ensuite renseigner `GOOGLE_CLIENT_ID` et
`APPLE_CLIENT_ID` dans le fichier `.env` (voir `.env.example`). Apple demande un compte
Apple Developer payant et une adresse de site en `https://`.

**À compléter avant la mise en ligne** : les coordonnées du support (fichier
`frontend/src/content/contact.ts`) et la relecture des conditions d'utilisation par un juriste.

---

## En cas de problème

| Message | Solution |
|---|---|
| `No module named 'django'` | Activez l'environnement : `venv\Scripts\activate` |
| `SECRET_KEY` introuvable | Le fichier `.env` manque : copiez `.env.example` en `.env` |
| `no such table` | Lancez `python manage.py migrate` |
| Port déjà utilisé | Un autre serveur tourne : fermez-le (Ctrl+C) ou utilisez `runserver 8001` |
| `Your local changes … would be overwritten` | Suivez l'étape 0 (sauvegarde puis `git checkout -f`) |
| `RPC failed` / `Connection was reset` | Coupure réseau passagère : relancez la commande |
| `No module named 'PIL'` ou `'cryptography'` | Nouvelles dépendances : `pip install -r requirements/dev.txt` |
| `Activate.ps1 cannot be loaded` | Lancez une fois : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
