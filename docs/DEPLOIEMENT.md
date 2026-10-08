# Plan de mise en production de NOUNOU+

Objectif : passer du développement (votre ordinateur) à un vrai service en ligne,
accessible aux familles et aux travailleurs de Lubumbashi, sans prendre de risque
inutile. On avance par étapes, avec un **pilote limité** avant l'ouverture à tous.

## 1. Préalables : ce qu'il faut avoir avant de commencer

### A. Décisions et comptes à créer (fondateur)

| Préalable | Pourquoi | Exemples / remarques |
|---|---|---|
| **Nom de domaine** | Adresse du site (ex. `nounouplus.cd` ou `.com`) | Acheter le domaine au nom d'ALTIS (pas d'un prestataire). |
| **Hébergeur** | Machine qui fait tourner le serveur | Option simple : un serveur virtuel (VPS) de 2 Go de mémoire (Hetzner, OVH, DigitalOcean…), ou une plateforme gérée (Render, Railway…). Choisir un centre de données proche (Europe ou Afrique du Sud) pour la vitesse. |
| **Base de données PostgreSQL** | Stocker les comptes, profils, messages… | Base gérée par l'hébergeur de préférence (sauvegardes automatiques). |
| **Stockage des fichiers** | Photos et documents d'identité | Disque du serveur avec sauvegarde, ou stockage « S3 » (ex. Cloudflare R2, Scaleway, OVH). Les documents ne doivent **jamais** être publics. |
| **Fournisseur SMS** | Codes de connexion par téléphone | Vérifier la couverture des opérateurs en RDC (Vodacom, Orange, Airtel, Africell), le prix par SMS et le nom d'expéditeur « NOUNOU+ ». Exemples à comparer : Africa's Talking, Twilio, un agrégateur local. |
| **Service d'envoi d'e-mails** | Confirmation d'adresse, mot de passe oublié | Brevo, Mailgun, Amazon SES… Configurer SPF / DKIM sur le domaine pour éviter les spams. |
| **Comptes Google et Apple développeur** (facultatif au départ) | Connexion avec Google / Apple | Google : gratuit. Apple : 99 $ / an, nécessaire aussi pour l'application iPhone. |
| **Adresse et téléphone du support** | Écran Aide, signalement de faille | À me transmettre pour remplacer les valeurs provisoires. |
| **Textes juridiques validés** | Conditions d'utilisation, confidentialité | Relecture par un juriste en RDC (protection des données personnelles, documents d'identité). |
| **Équipe de validation** | Valider documents, photos, références, signalements | Au moins 1 à 2 personnes formées, avec des comptes admin protégés. |

### B. Corrections techniques obligatoires (moi)

- ~~Corriger les failles **élevées** et le **lot 1** de `docs/AUDIT_SECURITE_2026-10.md`~~ :
  fait (voir la section « État des corrections » de l'audit).
- Brancher le **vrai fournisseur SMS** dans `apps/accounts/sms.py`. Le reste est déjà prêt :
  code aléatoire, haché, valable 10 minutes, 5 essais maximum, sans réponse différente selon
  que le numéro est inscrit ou non.
- Permettre le stockage des fichiers chez un fournisseur « S3 » si ce choix est fait.
- Ajouter la **suppression du compte** par l'utilisateur (exigée aussi par Google
  Play et l'App Store pour l'application mobile).
- Ajouter la double authentification pour l'équipe d'administration (recommandé).
- Ajouter un **suivi des erreurs** (ex. Sentry) et une **page de santé** pour la
  surveillance.

## 2. Architecture cible (simple, sans Docker pour démarrer)

```
Internet ──HTTPS──► nginx (certificat Let's Encrypt)
                      ├── /            → application React (fichiers construits)
                      ├── /api/        → gunicorn → Django (config.settings.prod)
                      └── /<ADMIN_URL> → gunicorn → Django (administration)
                     Django ──► PostgreSQL (non exposée sur Internet)
                     Django ──► stockage des fichiers (privé)
                     Django ──► fournisseur SMS / e-mail
```

L'application et l'API sont sur le **même domaine** : aucun accès « CORS » à ouvrir.

## 3. Étapes

### Étape 0 : préparer le code (1 à 2 semaines)
1. Corriger le lot 1 de l'audit, puis les décisions du lot 2.
2. Brancher le SMS et l'e-mail réels.
3. Écrire un script de déploiement répétable : installer, migrer, construire
   l'application, redémarrer.

### Étape 1 : environnement de test en ligne, « préproduction » (quelques jours)
1. Créer le serveur, la base PostgreSQL et le domaine `test.<votre-domaine>`.
2. Variables d'environnement, **sur le serveur uniquement**, jamais dans Git :
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`, réglée dans le service, pas
     seulement dans `.env` ;
   - nouvelle `SECRET_KEY` ;
   - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` ;
   - `NUM_PROXIES=1` ;
   - `ADMIN_URL` non évidente ;
   - `DB_*` avec `DB_SSLMODE=require` ;
   - `EMAIL_*`, `FRONTEND_URL`, identifiants SMS.
3. Exécuter `pip install -r requirements/prod.txt`, `python manage.py migrate`,
   `python manage.py createcachetable` et `python manage.py check --deploy`.
4. Faire tourner Django avec gunicorn, servi par nginx avec HTTPS. Régler
   `client_max_body_size 6m` et l'en-tête `frame-ancestors 'none'`.
5. Planifier une tâche quotidienne `flushexpiredtokens` et des **sauvegardes
   chiffrées** de la base et des fichiers. Faire un essai de restauration.
6. Tester tout le parcours avec de vrais téléphones et de vrais SMS (voir
   `docs/GUIDE_ESSAI.md`).

### Étape 2 : pilote fermé (2 à 4 semaines)
- 20 à 50 familles et travailleurs invités à Lubumbashi.
- L'équipe valide les documents et suit les signalements chaque jour.
- Surveiller : erreurs, coût des SMS, temps de réponse sur réseau mobile, retours
  des utilisateurs.
- Corriger, puis refaire un contrôle de sécurité rapide.

### Étape 3 : ouverture publique
- Domaine principal, communication, publication de l'application Android si elle
  est prête (voir `docs/APPLI_MOBILE.md`).
- Surveillance : alerte si le site tombe, revue hebdomadaire du journal
  `nounou.security`, mises à jour de sécurité mensuelles (Django, bibliothèques).

## 4. Liste de contrôle du jour J

- [ ] `DEBUG` désactivé, réglages `prod` vérifiés au démarrage
- [ ] Nouvelle clé secrète, jamais commitée
- [ ] HTTPS actif, redirection de `http` vers `https`
- [ ] Le code `123456` ne fonctionne pas (test)
- [ ] Adresse d'administration changée, comptes de l'équipe avec mots de passe forts
- [ ] Sauvegarde automatique faite **et** restauration testée
- [ ] SMS et e-mails reçus sur de vrais téléphones et boîtes
- [ ] Conditions d'utilisation et coordonnées du support à jour
- [ ] Alerte de disponibilité et suivi des erreurs actifs

## 5. Coûts mensuels indicatifs (à confirmer)

- **Serveur et base gérée** : environ 15 à 50 $ par mois selon l'hébergeur.
- **Domaine** : environ 10 à 40 $ par an.
- **SMS** : le poste le plus variable. Le prix par SMS vers la RDC est à négocier,
  à multiplier par le nombre de connexions.
- **E-mails** : souvent gratuit jusqu'à quelques milliers par mois.
- **Apple développeur** : 99 $ par an. **Google Play** : 25 $, une seule fois.
