# Audit de sécurité NOUNOU+ — octobre 2026

Cet audit couvre le serveur (Django) et l'application (React), dans l'état de la
branche `main` après la fusion de la PR #15. Il complète `docs/SECURITE.md`.

Trois relectures indépendantes ont été faites :
1. droits d'accès et confidentialité des données ;
2. connexion, sessions et limites d'essais ;
3. fichiers envoyés, réglages du serveur, application, bibliothèques et historique Git.

Chaque faille marquée « confirmée » a été reproduite avec un vrai test sur une
copie locale. Aucune donnée réelle n'a été touchée. Ce document ne dit pas que le
projet est « sûr à 100 % » : il liste ce qui a été trouvé, ce qui protège déjà, et
ce qu'il reste à corriger.

## 1. Bilan général

- **Aucune faille critique** n'est exploitable aujourd'hui, car l'application n'est
  pas encore en ligne et les codes SMS sont désactivés en production.
- **3 failles élevées** doivent être corrigées **avant** la mise en ligne.
- **10 failles moyennes** sont à corriger avant ou pendant la phase pilote.
- **Les protections de base sont solides** : chaque utilisateur ne voit que ses
  propres données, les coordonnées restent cachées avant un accord mutuel, les
  fichiers sont contrôlés, et aucune bibliothèque utilisée n'a de faille connue
  (`pip-audit` et `npm audit` ne signalent rien).

## 2. Failles à corriger

Niveaux : **Élevée** = un pirate peut prendre un compte ou bloquer quelqu'un ;
**Moyenne** = fuite d'information ou abus possible ; **Faible** = risque limité ou
seulement dans un cas particulier.

### Élevées (bloquantes pour la mise en ligne)

| # | Faille | Ce qu'un pirate peut faire | Correction |
|---|---|---|---|
| E1 | Si la variable `DJANGO_SETTINGS_MODULE` est oubliée sur le serveur, le site démarre en **mode développement** (`config/wsgi.py`, `manage.py`). Écrire cette variable dans `.env`, comme le suggère `.env.example`, ne suffit pas. | En mode développement, le code SMS `123456` fonctionne pour tous les comptes. Le pirate se connecte donc à n'importe quel compte, y compris ceux de l'équipe. **Confirmée.** | Le serveur refuse de démarrer sans réglage explicite ; corriger `.env.example`. |
| E2 | Quelqu'un peut **retirer l'adresse e-mail d'un autre compte** tant qu'elle n'est pas confirmée (`apps/accounts/emails.py`). | Il s'inscrit avec l'e-mail d'une victime qui n'a pas encore cliqué sur le lien de confirmation. La victime perd son e-mail : elle ne peut plus se connecter ni récupérer son mot de passe. **Confirmée.** | Garder la nouvelle adresse « en attente » jusqu'au clic sur le lien, sans toucher aux autres comptes. |
| E3 | Le **numéro de téléphone n'est jamais vérifié** lors d'une inscription par e-mail ou par Google / Apple. | Il prend le numéro de quelqu'un d'autre, se fait passer pour lui auprès des familles, et empêche le vrai propriétaire de s'inscrire. Quand les SMS seront actifs, le vrai propriétaire tomberait dans le compte du pirate. **Confirmée.** | Considérer un numéro comme « pris » seulement après un code SMS ; ne pas montrer un numéro non vérifié. |

### Moyennes

| # | Faille | Correction proposée |
|---|---|---|
| M1 | Un **refus** peut se deviner : la date de mise à jour du match change et le match remonte dans la liste. **Confirmée.** | Ne montrer que la date des actions visibles par chaque personne. |
| M2 | **Clics simultanés** : si une famille clique « intéressé » au même moment où la nounou clique « refuser », le refus peut être perdu et le téléphone révélé. **Confirmée.** | Verrouiller la ligne pendant la mise à jour. |
| M3 | **N'importe quel compte travailleur**, même non vérifié et sans profil, peut parcourir toutes les familles (prénom, quartier, budget, description des besoins) et toutes les offres. **Confirmée.** | **Décision du fondateur** : réserver ces listes aux travailleurs vérifiés, ou au moins à ceux qui ont un profil. |
| M4 | **Savoir si un numéro ou un e-mail est inscrit** : certains messages d'erreur le révèlent (inscription par e-mail, Google / Apple, changement d'e-mail, demande de code SMS en production). **Confirmée.** | Réponse identique dans tous les cas. |
| M5 | **Changement d'e-mail sans limite d'envois** : 50 demandes donnent 50 e-mails envoyés. Cela peut servir à harceler quelqu'un et à abîmer la réputation de l'adresse d'envoi. **Confirmée.** | Ajouter la limite `email_send` déjà prévue. |
| M6 | **Jeton volé = compte volé pour de bon** : sur un compte sans mot de passe (SMS ou Google), on peut changer l'e-mail et créer un mot de passe sans se reconnecter. **Confirmée.** | Demander une connexion récente avant ces deux actions, et prévenir l'utilisateur. |
| M7 | Une **petite image piégée** (150 Ko) consomme environ 380 Mo de mémoire au traitement. Quelques envois en parallèle peuvent faire tomber un petit serveur. **Confirmée.** | Abaisser la taille maximale en pixels ; limiter les formats lus. |
| M8 | Le mode hors connexion de l'application peut **mémoriser une page d'administration ou un document d'identité** à la place de la page d'accueil, si un membre de l'équipe utilise le même navigateur. | Ne mémoriser que les pages de l'application elle-même. |
| M9 | **Codes SMS pas prêts pour la production** : code stocké en clair, sans expiration ni nombre d'essais par code. Ce n'est pas actif aujourd'hui. | À faire en même temps que le branchement du vrai fournisseur SMS (voir `docs/DEPLOIEMENT.md`). |
| M10 | **Administration sans protection contre les essais de mots de passe**, ni double authentification. L'adresse reste `admin/` par défaut. | Limite d'essais et double authentification pour l'équipe ; refuser de démarrer si l'adresse est restée `admin/`. |

### Faibles et informations

- Les avis d'un travailleur non vérifié restent lisibles si l'on connaît son
  numéro de profil.
- La photo validée d'un compte suspendu reste accessible à qui possède son lien,
  et reste en cache jusqu'à 24 h.
- La durée de connexion révèle si un e-mail existe (0,5 s contre 0,004 s).
- Les documents d'identité s'ouvrent directement dans l'administration ; il vaut
  mieux les télécharger.
- La connexion à la base PostgreSQL n'exige pas le chiffrement par défaut.
- Les jetons de connexion sont gardés dans le navigateur (`localStorage`). Aucune
  faille XSS n'a été trouvée, mais des cookies `HttpOnly` seraient plus sûrs
  (décision B5).
- L'ancienne clé secrète de développement est dans l'historique Git (dépôt privé)
  **et toujours dans votre fichier `.env` local**. Elle ne doit jamais servir en
  production. Générez-en une nouvelle, même pour le développement.
- L'historique Git contient aussi une ancienne base SQLite de test (1 compte, un
  numéro de téléphone) et le dossier `venv`.
- `pytest` 8.3.2, utilisé seulement pour les tests, a une faille connue : mettre à
  jour vers 9.0.3 ou plus.
- Une session active n'expire jamais tant qu'on l'utilise. Il n'y a pas de durée
  maximale.
- Une fois un accord mutuel conclu, si l'autre personne se retire, la conversation
  se ferme. Cela révèle forcément le retrait : c'est une limite inhérente à la règle
  « un refus n'est jamais révélé ».

## 3. Ce qui protège déjà (vérifié)

- **Accès** : chaque adresse de l'API filtre selon l'utilisateur connecté. Modifier
  un identifiant dans l'URL renvoie « introuvable ». Personne ne peut se donner le
  rôle admin ni le badge « vérifié ».
- **Confidentialité** : le nom complet et le téléphone ne sont visibles qu'après un
  accord mutuel. Les documents et les références ne sont vus que par l'équipe. La
  messagerie n'est possible qu'entre personnes ayant un accord mutuel.
- **Sessions** : jeton d'accès de 10 minutes, renouvellement à usage unique,
  déconnexion après 30 minutes d'inactivité, révocation immédiate des comptes
  suspendus, et déconnexion de tous les appareils après un changement de mot de
  passe.
- **Mot de passe oublié** : lien signé, à usage unique, envoyé seulement à une
  adresse confirmée.
- **Google / Apple** : jeton vérifié avec les clés officielles. Un compte n'est
  relié automatiquement que si son e-mail est confirmé.
- **Fichiers** : contenu réel contrôlé, photos réencodées (position GPS supprimée),
  noms aléatoires, aucun accès direct aux dossiers. Aucune faille d'accès aux
  fichiers par l'adresse (`../`) : testé.
- **Navigateur** : politique CSP stricte, aucun endroit où du texte d'utilisateur
  est interprété comme du code, pas de redirection ouverte.
- **Réglages de production** : `DEBUG` désactivé, HTTPS obligatoire, HSTS, cookies
  sécurisés, clé secrète obligatoire, CORS fermé, documentation de l'API réservée à
  l'équipe. `check --deploy` ne signale que deux options volontairement laissées au
  choix.
- **Vérifications automatiques** : la CI a les droits en lecture seule, aucun
  secret n'est dans le code, et `pip-audit` et `npm audit` ne signalent rien.

## 4. Ordre de correction proposé

1. **Lot 1, avant toute mise en ligne** : E1, E2, E3, M5, M6, M7, M8, plus la limite
   d'essais sur l'administration (M10).
2. **Lot 2, décision du fondateur** : M3 (qui peut voir les familles et les offres),
   B5 (cookies), B6 (double authentification pour l'équipe), B7 (suppression du
   compte).
3. **Lot 3, avec le vrai fournisseur SMS** : M4 et M9.
4. **Lot 4, petites corrections** : M1, M2 et les points faibles.

## 5. État des corrections (mise à jour)

**Corrigées et couvertes par des tests automatiques :**

- **Élevées** : E1, E2, E3.
  - E3 a été corrigée selon le choix du fondateur : code SMS obligatoire avant tout accès, et le
    vrai titulaire du numéro récupère le compte.
- **Moyennes** : M1, M2, M3, M4, M5, M6, M7, M8, M9, M10.
  - M3 a été corrigée selon le choix du fondateur : familles et annonces réservées aux
    travailleurs vérifiés.
  - M4 : les réponses ne révèlent plus si un numéro ou un e-mail est inscrit, y compris en
    production sans SMS.
  - M9 : le code SMS est prêt pour la production ; il ne reste qu'à brancher le fournisseur.
  - M10 : 10 essais de connexion par 15 minutes, et une adresse d'administration obligatoire
    en production. La double authentification reste à décider.
- **Faibles** :
  - avis d'un travailleur non vérifié ;
  - photo d'un compte suspendu, dont le cache passe de 24 h à 1 h ;
  - durée de connexion identique pour un e-mail connu ou inconnu ;
  - documents téléchargés au lieu d'être ouverts dans l'administration ;
  - connexion chiffrée imposée vers une base distante ;
  - Pillow limité à trois formats ;
  - lignes du journal protégées ;
  - `pytest` mis à jour et vérifié par `pip-audit` dans la CI.

**Changement de fonctionnement à connaître :**

- L'inscription avec e-mail demande d'abord le code SMS. Le mot de passe et l'adresse sont
  enregistrés juste après.
- Une adresse e-mail ne permet de se connecter qu'une fois confirmée par le lien.
- Les anciens comptes de test dont le numéro n'a jamais été confirmé doivent saisir un code SMS.
  Si quelqu'un d'autre que le titulaire avait ajouté un mot de passe, un e-mail ou un compte
  Google / Apple, ces accès sont retirés.

**Restent ouvertes :**

- Décisions du fondateur :
  - B5 : cookies `HttpOnly` ;
  - B6 : double authentification pour l'équipe ;
  - B7 : suppression du compte, obligatoire pour les magasins d'applications.
- Points faibles :
  - aucune durée maximale de session ;
  - réutilisation simultanée d'un même jeton de renouvellement ;
  - envoi des e-mails pendant la requête au lieu d'en arrière-plan ;
  - listes de messages et de favoris sans pagination ;
  - masque du téléphone qui laisse voir l'opérateur et le dernier chiffre ;
  - actions de la CI référencées par version plutôt que par empreinte.
- Limite inhérente : après un accord mutuel, le retrait de l'autre personne se voit forcément.
