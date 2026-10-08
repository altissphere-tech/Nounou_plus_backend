# Parcours utilisateurs NOUNOU+

Ce document décrit les parcours clés, étape par étape, avec pour chacun ce qui peut
bloquer et ce qui est vérifié automatiquement (`frontend/src/test/journeys.test.tsx`).
Il sert de référence pour les tests avec de vrais utilisateurs
(voir `docs/GUIDE_TEST_UTILISATEURS.md`).

## 1. Inscription d'une famille ou d'un travailleur (par téléphone)

| Étape | Écran | Ce que fait la personne | Point d'attention |
|---|---|---|---|
| 1 | Accueil | Touche « Créer un compte » | Le bouton doit se voir sans faire défiler l'écran |
| 2 | Inscription | Choisit « Une famille » ou « Un travailleur » | Le choix doit être compris sans lire le petit texte |
| 3 | Inscription | Saisit son numéro (`08…` ou `+243…`) | Les deux formats sont acceptés |
| 4 | Code | Saisit le code reçu par SMS | SMS lent ou pas reçu : « Renvoyer le code » |
| 5 | Accueil connecté | Voit « Prochaine étape : créer mon profil » | |

✅ **Test automatique** : rôle, numéro, code, puis arrivée sur l'accueil.

## 2. Inscription avec e-mail et mot de passe

1. Il y a les mêmes étapes que le parcours 1, avec en plus l'onglet « E-mail » : l'adresse et le
   mot de passe se saisissent sur l'écran d'inscription.
2. **Le code SMS est toujours demandé d'abord.** Sans lui, aucun compte n'est utilisable.
3. Juste après le code, le mot de passe et l'adresse sont enregistrés. Un lien de
   confirmation part à l'adresse.
4. L'accueil affiche « Confirmez votre adresse e-mail ». Tant que le lien n'est pas
   ouvert, l'adresse ne permet pas de se connecter.

✅ **Test automatique** : rien n'est envoyé avant le code, puis le mot de passe et
l'adresse sont enregistrés dans le bon ordre.

## 3. Connexion

- **Par téléphone** : numéro, puis code SMS.
- **Par e-mail** : adresse confirmée et mot de passe. Si le numéro du compte n'a jamais été
  confirmé, un code SMS est envoyé et demandé avant d'entrer.
- **Google / Apple** : à la première fois, il faut choisir son rôle et donner son numéro,
  puis saisir le code SMS. Le compte Google / Apple est relié ensuite.

✅ **Test automatique** : connexion par e-mail avec un numéro jamais confirmé, qui mène au code.

## 4. Famille : trouver une personne de confiance

| Étape | Écran | Ce que fait la personne |
|---|---|---|
| 1 | Profil | Crée son profil famille : quartier, besoins, budget |
| 2 | Rechercher | Filtre par service (Nounou, Ménage, Cuisine) et par quartier |
| 3 | Fiche | Lit le parcours, le score de confiance et les avis |
| 4 | Fiche | Touche « Je suis intéressé(e) » |
| 5 | Relations | Attend la réponse. Un refus n'est jamais montré : la demande reste « en attente » |
| 6 | Relations | En cas d'accord mutuel : nom complet, téléphone et messagerie apparaissent |

✅ **Test automatique** : fiche, intérêt envoyé, et téléphone toujours caché avant l'accord.

**Point d'attention** : le badge « Vérifié » doit être compris comme « documents
contrôlés par l'équipe », et non comme une garantie.

## 5. Travailleur : trouver un emploi

| Étape | Écran | Ce que fait la personne |
|---|---|---|
| 1 | Profil | Crée son profil : services, expérience, salaire souhaité, quartier |
| 2 | Vérification | Envoie sa pièce d'identité et ajoute jusqu'à 3 références |
| 3 | Attente | Tant que l'équipe n'a pas validé, les annonces des familles restent cachées, avec un message qui l'explique |
| 4 | Annonces | Une fois vérifié, consulte les annonces et touche « Répondre à l'annonce » |
| 5 | Relations | Même suite que pour les familles |

✅ **Test automatique** : un travailleur non vérifié voit le message, jamais les familles.

## 6. Après l'accord mutuel

1. **Messagerie** : premiers échanges, avec le rappel des conseils de sécurité.
2. **Appel** : bouton « Appeler ».
3. **Avis** : possible 7 jours après l'accord, une fois par personne.
4. **Signalement** : depuis la fiche ou la conversation. La personne signalée ne sait pas qui l'a signalée.

## 7. Sécurité du compte

- Déconnexion après 30 minutes d'inactivité, avec un avertissement 1 minute avant.
- Écran « Sécurité » :
  - ajouter ou changer son e-mail et son mot de passe ;
  - se déconnecter de tous les appareils.
- Mot de passe oublié : un lien est envoyé, seulement à une adresse confirmée.
