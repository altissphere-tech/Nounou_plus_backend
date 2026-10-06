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

## Commandes utiles

| Commande | Rôle |
|---|---|
| `npm run dev` | Lance l'application en mode développement |
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
└── styles.css    → couleurs et mise en forme (couleurs de la marque en haut du fichier)
```

**Ajouter ou modifier un texte** : le changer dans `src/i18n/fr.ts` **et** `src/i18n/en.ts`
(un test vérifie que les deux langues ont toujours les mêmes textes).
