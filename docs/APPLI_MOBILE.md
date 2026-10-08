# Plan pour l'application mobile NOUNOU+

## 1. Point de départ

- Le **serveur (API Django)** est déjà prêt pour une application mobile : il parle
  en JSON, utilise des jetons de connexion, et toute la sécurité est faite côté
  serveur. On le **réutilise tel quel**.
- L'**application React** est déjà une PWA : on peut l'« installer » sur
  l'écran d'accueil d'un téléphone Android depuis le navigateur. Elle est adaptée
  aux téléphones et a un mode hors connexion minimal.

Il n'y a donc **pas besoin de tout réécrire**. La question est : comment passer de
cette application web à une application présente dans les magasins Google Play et
App Store.

## 2. Trois options

| Option | Principe | Code réutilisé | Délai indicatif | Avantages | Limites |
|---|---|---|---|---|---|
| **A. PWA seule** | On garde l'application web installable | 100 % | Déjà disponible | Aucun coût, mises à jour instantanées | Pas dans les magasins ; notifications limitées sur iPhone |
| **B. Capacitor** *(recommandée)* | On « emballe » l'application React existante dans une vraie application Android / iPhone | ~90 % | 3 à 6 semaines | Même code pour web, Android et iPhone ; présence dans les magasins ; notifications, appareil photo, stockage sécurisé | Un peu moins fluide qu'une application 100 % native |
| **C. React Native (Expo)** | On réécrit les écrans en composants mobiles | ~40 % (API, types, logique, textes FR/EN) | 2 à 4 mois | Sensation 100 % native | Deux applications à maintenir (web et mobile) |

**Recommandation : A tout de suite, puis B en commençant par Android.** La grande
majorité des téléphones à Lubumbashi sont des Android. iPhone viendra ensuite, avec
le même code. L'option C ne vaut la peine que si l'application devient très
complexe, par exemple avec de la vidéo ou de la géolocalisation en direct.

## 3. Préalables

- Les **corrections de sécurité du lot 1** (`docs/AUDIT_SECURITE_2026-10.md`) et la
  **mise en ligne du serveur** (`docs/DEPLOIEMENT.md`). L'application mobile a
  besoin d'une API en ligne, en HTTPS.
- **Compte Google Play Console** (25 $, une seule fois). Pour iPhone, **Apple
  Developer** (99 $ par an) et un Mac, ou un service de compilation en ligne.
- **Suppression du compte depuis l'application** : obligatoire pour les deux
  magasins.
- **Politique de confidentialité** publiée sur le site, plus le formulaire
  « sécurité des données » de Google Play. Il faut y déclarer le téléphone, les
  photos et les documents d'identité.
- **Icône, captures d'écran et description** dans les magasins, en français et en
  anglais.
- Si la connexion Google est proposée sur iPhone, **Apple exige aussi « Se
  connecter avec Apple »**. C'est déjà prévu dans le code.

## 4. Étapes (option B, Capacitor)

1. **Préparer l'API pour le mobile** (environ 1 semaine)
   - Autoriser uniquement les origines de l'application mobile
     (`capacitor://localhost`, `https://localhost`), sans cookies et jamais `*`.
   - Liens « mot de passe oublié » et « confirmer l'e-mail » qui ouvrent
     l'application (App Links Android / Universal Links iPhone).
   - Notifications : envoi par Firebase Cloud Messaging (Android et iPhone), en
     plus des notifications dans l'application.
2. **Emballer l'application React** (environ 1 semaine)
   - Ajouter Capacitor au dossier `frontend/`, puis créer les projets Android et
     iOS.
   - Garder les jetons dans le **stockage sécurisé du téléphone** (Keystore /
     Keychain) plutôt que dans le stockage du navigateur.
   - Utiliser l'appareil photo et la galerie pour la photo de profil et les
     documents.
   - Garder la déconnexion après 30 minutes d'inactivité.
3. **Adapter aux réseaux mobiles de la RDC** (en continu)
   - Images légères, messages clairs quand le réseau coupe, nouvel essai
     automatique.
   - Tester sur des téléphones Android d'entrée de gamme.
4. **Tests et bêta fermée** (1 à 2 semaines)
   - Google Play « test interne / fermé » avec les participants du pilote.
5. **Publication**
   - Google Play d'abord, puis l'App Store (la validation d'Apple prend quelques
     jours et demande souvent des ajustements).
6. **Après la publication**
   - Mises à jour régulières. Les corrections d'écrans peuvent passer par le site
     web, les changements natifs passent par les magasins.

## 5. Ce qui ne change pas

- Les règles métier restent sur le serveur : coordonnées cachées avant l'accord
  mutuel, refus jamais révélé, badge « vérifié » qui n'est pas une garantie.
- Une seule base de code pour l'interface (web + Android + iPhone), donc une
  seule chose à maintenir.
