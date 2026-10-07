# Sécurité de NOUNOU+

Ce document résume les protections en place et ce qu'il reste à faire avant la
mise en ligne. Il ne prétend pas que l'application est « sûre à 100 % » : il liste
les risques identifiés, les contrôles mis en place et les risques restants.

## Protections en place

| Domaine | Ce qui protège |
|---|---|
| Accès aux données | Chaque adresse de l'API vérifie côté serveur le rôle et le propriétaire (un identifiant modifié renvoie 404). Champs sensibles (`is_verified`, statut des documents…) non modifiables par les utilisateurs. |
| Confidentialité | Nom complet et téléphone cachés avant un accord mutuel ; refus jamais révélé ; documents et références vus par l'équipe seulement ; photos publiques seulement après validation. |
| Connexion | Code SMS, e-mail + mot de passe (8 caractères minimum, mots de passe courants refusés), Google / Apple (jeton vérifié avec les clés publiques du service). |
| Adresse e-mail | Confirmée par lien avant de servir à « mot de passe oublié » ou à relier un compte Google / Apple (empêche la prise de contrôle d'un compte). |
| Sessions | Jeton d'accès de 30 min ; jeton de renouvellement à usage unique (7 jours) ; déconnexion révoquée côté serveur ; changement de mot de passe = autres appareils déconnectés ; « Se déconnecter de tous les appareils ». Comptes suspendus bloqués immédiatement. |
| Abus | Limites d'essais : 5 SMS / heure / numéro, 10 essais de code / heure / numéro, 10 inscriptions / heure / appareil, connexions, messages, signalements, envois de fichiers (voir `THROTTLE_RATES`). L'adresse IP ne peut pas être falsifiée par un en-tête. |
| Réponses sans indice | La demande de code et l'inscription par téléphone répondent pareil que le numéro soit inscrit ou non. |
| Fichiers | Taille limitée (5 Mo) ; contenu réel contrôlé (un faux PDF est refusé) ; photos réencodées (GPS supprimé, images piégées refusées) ; noms aléatoires ; documents jamais servis publiquement. |
| Navigateur | Politique de sécurité du contenu (CSP) dans la version finale ; en-têtes de sécurité sur l'API (`no-store`, CSP stricte, `nosniff`, `DENY`, `Permissions-Policy`) ; le mode hors connexion ne garde jamais de réponse de l'API. |
| Journal | `nounou.security` : connexions, échecs, codes refusés, limites atteintes, mots de passe changés, décisions sur les signalements — sans mot de passe, code, jeton ni identifiant en clair. |
| Dépendances | Django 5.2 LTS ; vérification automatique `pip-audit` et `npm audit` à chaque pull request (`.github/workflows/ci.yml`, droits en lecture seule). |

## Avant la mise en ligne (obligatoire)

1. **Nouvelle clé secrète** : générer une `SECRET_KEY` neuve pour la production.
   Ne jamais réutiliser une clé qui a été commitée (l'historique Git contient l'ancienne
   clé de développement du début du projet).
2. **Variables d'environnement** (voir `.env.example`) : `ALLOWED_HOSTS`, `NUM_PROXIES=1`
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
7. **Vrai fournisseur SMS** : codes aléatoires, stockés hachés, valables 10 minutes,
   à usage unique (le code fixe `123456` reste réservé au développement).

## Recommandé avant la mise en ligne (décision du fondateur)

- Jetons de connexion en cookies sécurisés (HttpOnly) au lieu du stockage du navigateur.
- Double authentification pour les comptes de l'équipe (administration).
- Suppression du compte par l'utilisateur lui-même et export de ses données.
- Relecture des conditions d'utilisation par un juriste (protection des données
  personnelles en RDC).

## Signaler une faille

Écrire à l'adresse du support (voir `frontend/src/content/contact.ts`) sans publier
les détails.
