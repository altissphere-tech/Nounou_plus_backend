# Mentions légales et Politique de confidentialité

Textes fournis par le fondateur le 8 octobre 2026, intégrés dans l'application :

- `/mentions-legales` : éditeur, rôle de la plateforme, propriété intellectuelle, hébergement ;
- `/confidentialite` : politique de confidentialité (23 sections) ;
- `/conditions` : conditions d'utilisation, qui renvoient maintenant à la politique.

Le contenu se trouve dans `frontend/src/content/legal.ts` (français et anglais). La version
française fait foi. **Les textes doivent encore être relus par un juriste en RDC**, d'où le
bandeau « Brouillon » en haut de chaque page.

## Corrections apportées avant intégration

Une politique de confidentialité doit décrire **exactement** ce que fait l'application.
Annoncer une donnée qu'on ne collecte pas, ou taire une donnée qu'on collecte, est une erreur
juridique. Voici ce qui a été corrigé :

| # | Texte fourni | Correction | Raison |
|---|---|---|---|
| 1 | « RCCM : RCCM CD/LSH/RCCM/26-B-00091 » | « RCCM : CD/LSH/RCCM/26-B-00091 » | Préfixe « RCCM » écrit deux fois |
| 2 | Réservations et prestations gérées par la plateforme | Fonctions réelles : profils, recherche, annonces, intérêt, accord mutuel, messagerie, avis, signalements | Ces fonctions n'existent pas |
| 3 | Post-nom, date de naissance, sexe | Retirés, avec la mention « nous ne collectons pas » | Ces champs n'existent pas dans l'application |
| 4 | Données de paiement, section 8 « à compléter » | « Aucun paiement via NOUNOU+ » | Aucun paiement n'existe |
| 5 | Géolocalisation de l'appareil | Seul le quartier saisi est utilisé, pas de GPS | Pas de GPS dans l'application |
| 6 | Pages consultées, statistiques | « Aucun outil de statistiques ni de publicité » ; journaux techniques et de sécurité décrits | Pas d'outil de statistiques |
| 7 | Section 17 : « nom et prénom » des travailleurs visibles | Prénom et initiale du nom avant l'accord mutuel ; nom complet et téléphone après | Règle de confidentialité de l'application |
| 8 | « Vérifié ne constitue pas nécessairement une garantie absolue » | « Le badge “Vérifié” ne constitue pas une garantie » | Règle du projet, cohérente avec les conditions d'utilisation |
| 9 | Accès de l'équipe aux messages non mentionné | Ajouté : l'équipe peut consulter les messages en cas de signalement ou pour la sécurité | Transparence : l'administration le permet |
| 10 | Cookies « à compléter » | Pas de cookie publicitaire ni de statistiques ; stockage local (connexion, langue) ; cookies de l'espace équipe | Fonctionnement réel |
| 11 | « [Lien vers la Politique de confidentialité] » | Vrai lien vers `/confidentialite` | Lien manquant |
| 12 | Hébergeur, prestataires, transferts « à compléter » | « Précisé au moment de la mise en ligne » ; types de prestataires listés (hébergement, SMS, e-mail, Google / Apple) | Ne pas afficher « [à compléter] » au public |
| 13 | Nom du logiciel serveur (NGINX) | Retiré (seul HTTPS est mentionné) | Sécurité : ne pas annoncer les outils techniques utilisés |
| 14 | Mineurs : texte ambigu | Réservé aux 18 ans et plus, comme les conditions d'utilisation | Cohérence entre les textes |
| 15 | Durées de conservation vagues | Durées connues ajoutées (code SMS 10 min, photo refusée supprimée, déconnexion après 30 min) | Précision |
| 16 | Communications marketing | « Pas de messages publicitaires » ; accord demandé si cela change | Aucun envoi publicitaire |

« NOUNOU+ n'est pas l'employeur » est conservé et repris des conditions d'utilisation.

## Reste à faire (fondateur)

1. **Hébergeur** : à indiquer dans `HOSTING_PROVIDER` (`frontend/src/content/legal.ts`) dès
   qu'il est choisi, ainsi que la liste des prestataires (SMS, e-mail) en section 20.
2. **Relecture par un juriste** en RDC, notamment sur la loi applicable à la protection des
   données et le traitement des pièces d'identité.
3. **Mettre à jour ces textes à chaque nouvelle fonction** qui touche aux données : paiement,
   localisation, statistiques, publicité, suppression du compte dans l'application.
