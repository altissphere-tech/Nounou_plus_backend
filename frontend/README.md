# NOUNOU+ — Application (web, pour téléphone)

Application que les familles et les travailleurs utilisent sur leur téléphone.
Elle parle au backend Django (dossier parent) via l'API `/api/...`.

## Prérequis (une seule fois)

- **Node.js 22 LTS** : à télécharger sur https://nodejs.org (bouton « LTS »), puis installer.
  Vérification dans un nouveau PowerShell : `node --version`.

## Installation (une seule fois, et après chaque mise à jour)

```powershell
cd frontend
npm install
```

## Lancer l'application

Il faut **deux fenêtres PowerShell** :

1. **Le serveur** (à la racine du projet, avec le `venv` activé) :
   ```powershell
   python manage.py runserver
   ```
2. **L'application** (dans le dossier `frontend`) :
   ```powershell
   npm run dev
   ```

Puis ouvrez **http://localhost:5173** dans le navigateur. Astuce : dans Chrome, touche
`F12` puis l'icône téléphone pour voir l'application au format mobile.

En développement, le code SMS est toujours `123456`.

## Essayer sur votre téléphone (même Wi-Fi que le PC)

1. Fenêtre 1 (racine du projet) : `python manage.py runserver`
2. Fenêtre 2 (dossier `frontend`) : `npm run dev:phone`
3. Une ligne `Network: http://192.168.x.x:5173/` s'affiche : ouvrez **cette adresse**
   dans le navigateur du téléphone (le téléphone doit être sur le même Wi-Fi).

La première fois, Windows peut demander l'autorisation d'accès au réseau pour
Node.js : acceptez pour les **réseaux privés**.

## Installation sur l'écran d'accueil et mode hors connexion

L'application peut être **installée** sur le téléphone (icône NOUNOU+, plein écran)
et **s'ouvre même sans internet** (bandeau « Vous êtes hors connexion »). Les données
personnelles (profils, messages…) ne sont jamais gardées en mémoire sur le téléphone :
elles viennent toujours du serveur.

Ces deux fonctions ne sont actives que dans la **version finale**, et sur un téléphone
seulement une fois l'application **mise en ligne en HTTPS**. Pour les essayer sur le PC :

```powershell
npm run build
npm run preview
```

Puis ouvrez **http://localhost:4173** dans Chrome : une icône « Installer » apparaît
dans la barre d'adresse. (Le serveur Django doit aussi tourner.)

Après une modification de `public/sw.js`, augmentez `VERSION` en haut du fichier.

## Commandes utiles

| Commande | Rôle |
|---|---|
| `npm run dev` | Lance l'application en mode développement |
| `npm run dev:phone` | Idem, accessible depuis un téléphone du même Wi-Fi |
| `npm run preview` | Lance la version finale (après `npm run build`) |
| `npm test` | Lance les tests automatiques |
| `npm run build` | Prépare la version finale (dossier `dist/`) |
| `npm run lint` | Vérifie la qualité du code |

## Organisation du code

```
src/
├── api/          → appels au serveur (connexion, renouvellement du token)
├── auth/         → qui est connecté
├── i18n/         → textes en français (fr.ts) et en anglais (en.ts)
├── components/   → éléments communs (en-tête, logo, champ téléphone…)
├── pages/        → un fichier par écran
├── pwa/          → installation sur l'écran d'accueil, détection hors connexion
└── styles.css    → couleurs et mise en forme (couleurs de la marque en haut du fichier)
```

**Ajouter ou modifier un texte** : le changer dans `src/i18n/fr.ts` **et** `src/i18n/en.ts`
(un test vérifie que les deux langues ont toujours les mêmes textes).
