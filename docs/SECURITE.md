# Sécurité de NOUNOU+

Ce document résume les protections en place et ce qu'il reste à faire avant la
mise en ligne. Il ne prétend pas que l'application est « sûre à 100 % » : il liste
les risques identifiés, les contrôles mis en place et les risques restants.

## Protections en place

| Domaine | Ce qui protège |
|---|---|
| Accès aux données | Chaque adresse de l'API vérifie côté serveur le rôle et le propriétaire (un identifiant modifié renvoie 404). Champs sensibles (`is_verified`, statut des documents…) non modifiables par les utilisateurs. |
| Confidentialité | Nom complet et téléphone cachés avant un accord mutuel ; refus jamais révélé (ni par la date ni par l'ordre de la liste) ; deux décisions simultanées ne s'écrasent pas ; familles et annonces visibles seulement des travailleurs vérifiés ; documents et références vus par l'équipe seulement ; photos publiques seulement après validation (et plus du tout si le compte est suspendu). |
| Connexion | Code SMS, e-mail + mot de passe (8 caractères minimum, mots de passe courants refusés), Google / Apple (jeton vérifié avec les clés publiques du service). |
| Numéro de téléphone | Toujours confirmé par code SMS avant tout accès (inscription par téléphone, e-mail ou Google / Apple). Un compte au numéro non confirmé n'apparaît nulle part ; si le vrai titulaire du numéro saisit le code, les accès ajoutés par quelqu'un d'autre sont retirés. |
| Codes SMS | Aléatoires (en production), stockés sous forme d'empreinte, valables 10 minutes, 5 essais au plus, à usage unique. |
| Adresse e-mail | Reste « en attente » jusqu'au clic sur le lien : elle ne sert ni à se connecter, ni à « mot de passe oublié », ni à relier Google / Apple, et ne retire rien à personne. Une adresse déjà utilisée n'est pas signalée (son titulaire est seulement prévenu). |
| Actions sensibles | Créer un premier mot de passe ou changer d'e-mail : mot de passe actuel, ou connexion de moins de 10 minutes. |
| Sessions | Déconnexion après 30 min d'inactivité (avertissement 1 min avant ; aussi appliquée par le serveur quand l'application est fermée) ; jeton d'accès de 10 min ; jeton de renouvellement à usage unique ; déconnexion révoquée côté serveur ; changement de mot de passe = autres appareils déconnectés ; « Se déconnecter de tous les appareils ». Comptes suspendus bloqués immédiatement. |
| Abus | Limites d'essais : 5 SMS / heure / numéro, 10 essais de code / heure / numéro, 10 inscriptions / heure / appareil, connexions, messages, signalements, envois de fichiers (voir `THROTTLE_RATES`). L'adresse IP ne peut pas être falsifiée par un en-tête. |
| Réponses sans indice | La demande de code et l'inscription par téléphone répondent pareil que le numéro soit inscrit ou non. |
| Fichiers | Taille limitée (5 Mo) ; contenu réel contrôlé (un faux PDF est refusé) ; photos limitées à JPG / PNG / WEBP et 16 millions de pixels, réencodées (GPS supprimé, images piégées refusées) ; noms aléatoires ; documents jamais servis publiquement, téléchargés (jamais ouverts) dans l'administration. |
| Navigateur | Politique de sécurité du contenu (CSP) dans la version finale ; en-têtes de sécurité sur l'API (`no-store`, CSP stricte, `nosniff`, `DENY`, `Permissions-Policy`) ; le mode hors connexion ne garde jamais de réponse de l'API, ni de page d'administration ou de document. |
| Administration | 10 essais de mot de passe au plus par 15 minutes (par appareil et par identifiant) ; adresse obligatoirement changée en production. |
| Démarrage | Sans réglage explicite (`DJANGO_SETTINGS_MODULE`), le serveur refuse de démarrer au lieu de tourner en mode développement. En production, il refuse aussi une `ADMIN_URL` laissée à `admin/`. |
| Journal | `nounou.security` : connexions, échecs, codes refusés, limites atteintes, mots de passe changés, décisions sur les signalements — sans mot de passe, code, jeton ni identifiant en clair. |
| Dépendances | Django 5.2 LTS ; vérification automatique `pip-audit` et `npm audit` à chaque pull request (`.github/workflows/ci.yml`, droits en lecture seule). |

## Avant la mise en ligne (obligatoire)

1. **Nouvelle clé secrète** : générer une `SECRET_KEY` neuve pour la production.
   Ne jamais réutiliser une clé qui a été commitée (l'historique Git contient l'ancienne
   clé de développement du début du projet).
2. **Variables d'environnement** (voir `.env.example`) : `DJANGO_SETTINGS_MODULE=config.settings.prod`,
   `ALLOWED_HOSTS`, `NUM_PROXIES=1`
   derrière un proxy, `CSRF_TRUSTED_ORIGINS`, `ADMIN_URL`, base PostgreSQL, serveur e-mail.
3. `pip install -r requirements/prod.txt`, `python manage.py migrate`,
   `python manage.py createcachetable` (limites d'essais partagées).
4. **Tâche quotidienne** : `python manage.py flushexpiredtokens` (nettoie les jetons expirés).
5. **Serveur web** (nginx ou hébergeur) : HTTPS obligatoire ; en-tête
   `Content-Security-Policy: frame-ancestors 'none'` pour l'application ;
   `client_max_body_size 6m` ; servir l'application et l'API sur le **même domaine**
   (pas de CORS à ouvrir).
6. **PostgreSQL** : utilisateur dédié sans droit d'administration, base non exposée
   sur Internet, sauvegardes chiffrées et testées.
7. **Vrai fournisseur SMS** : à brancher dans `apps/accounts/sms.py` (les codes sont déjà
   aléatoires, stockés hachés, valables 10 minutes, 5 essais, à usage unique ; le code fixe
   `123456` reste réservé au développement). Sans fournisseur, l'inscription répond « indisponible ».

## Recommandé avant la mise en ligne (décision du fondateur)

- Jetons de connexion en cookies sécurisés (HttpOnly) au lieu du stockage du navigateur.
- Double authentification pour les comptes de l'équipe (administration).
- Suppression du compte par l'utilisateur lui-même et export de ses données.
- Relecture des conditions d'utilisation par un juriste (protection des données
  personnelles en RDC).

## Signaler une faille

Écrire à **support@nounou-plus.com** sans publier les détails.
