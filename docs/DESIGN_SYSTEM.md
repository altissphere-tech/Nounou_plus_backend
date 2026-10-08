# Design system NOUNOU+

Ce document est la référence du style de l'application (`frontend/`). Il a deux buts :

- que tous les écrans se ressemblent ;
- qu'une couleur ou un espacement se change à **un seul endroit**.

## Principes

1. **Téléphone d'abord**. L'application est conçue pour un écran de 360 px. Elle s'élargit
   à partir de 700 px (tablette), puis à partir de 1024 px (ordinateur, avec un menu à gauche).
2. **Légère**. Elle doit rester utilisable en 3G à Lubumbashi : pas d'image décorative lourde, une
   seule police, et chaque écran se télécharge seulement quand on l'ouvre.
3. **Lisible par tous**. Le contraste est d'au moins 4,5:1 pour le texte. Les zones tactiles font
   au moins 44 × 44 px. La sélection au clavier est toujours visible.
4. **Rassurante, jamais trompeuse**. Le badge « Vérifié » n'est jamais présenté comme une garantie.
5. **Sobre en mouvement**. Les animations sont courtes (120 à 320 ms) et désactivées si le téléphone
   demande moins d'animations.

## Où se trouve le style

```
frontend/src/styles.css          ← liste des fichiers, dans l'ordre (l'ordre compte)
frontend/src/styles/tokens.css   ← toutes les valeurs de référence (seul fichier avec des couleurs)
frontend/src/styles/*.css        ← un fichier par partie : base, mise en page, boutons, listes…
```

Le test `styles/designSystem.test.ts` échoue dans deux cas :

- une couleur est écrite en dur ailleurs que dans `tokens.css` ;
- un fichier de style n'est pas chargé par `styles.css`.

## Valeurs de référence (tokens)

### Couleurs

| Rôle | Token | Valeur |
|---|---|---|
| Marque (violet) | `--brand` / `--brand-dark` / `--brand-light` | #3b12b8 / #2a0c86 / #f0ebff |
| Accent (orange) | `--accent` / `--accent-light` / `--accent-dark` | #f5931e / #fff3e0 / #b86200 |
| Texte | `--text` / `--muted` / `--text-faint` | principal / secondaire / discret |
| Fonds | `--background` / `--surface` / `--surface-tint` | page / carte / champ |
| Bordures | `--border` / `--border-strong` | |
| Succès | `--success` / `--success-bg` | |
| Attention | `--warning-text` / `--warning-bg` / `--warning-border` | |
| Erreur | `--error` / `--error-bg` / `--error-border` | |
| Favori | `--favorite` / `--favorite-bg` | cœur |
| Pastilles d'initiales | `--avatar-1` à `--avatar-6` | texte blanc lisible sur chacune |

**Règle** : l'orange ne sert jamais pour du texte sur fond blanc, car il serait trop peu lisible.
On l'utilise pour les icônes, les badges et le « + », ou on prend `--accent-dark` pour du texte.

### Espacements

L'échelle va de 2 px en 2 px jusqu'à 16 px, puis de 4 px en 4 px :
`--space-0-5` (2) · `--space-1` (4) · `--space-1-5` (6) · `--space-2` (8) · `--space-2-5` (10) ·
`--space-3` (12) · `--space-3-5` (14) · `--space-4` (16) · `--space-5` (20) · `--space-6` (24) ·
`--space-8` (32) · `--space-10` (40) · `--space-12` (48) · `--space-14` (56).

### Arrondis

`--radius-xs` (6) · `--radius-sm` (12) · `--radius-md` (16) · `--radius-lg` (20, cartes) ·
`--radius-xl` (32, bas des en-têtes violets) · `--radius-pill` (boutons et pastilles).

### Texte

La police est **Nunito** (`--font-family`). Les tailles disponibles sont :
`--font-xs` (12 px) · `--font-sm` (13,6) · `--font-md` (14,7) · `--font-base` (16) · `--font-lg` (17,6) ·
`--font-xl` (20) · `--font-2xl` (24) · `--font-3xl` (32) · `--font-4xl` (38,4).

### Ombres

| Token | Usage |
|---|---|
| `--shadow` | Cartes |
| `--shadow-sm` | Petits éléments |
| `--shadow-lg` | Fenêtres |
| `--shadow-brand` | Bouton principal |
| `--shadow-up` | Barre du bas |

### Mouvement

- Durées : `--duration-fast` (120 ms), `--duration` (200 ms), `--duration-slow` (320 ms).
- Courbe : `--ease-out`.

## Composants

| Composant | Fichier | Usage |
|---|---|---|
| Boutons | `.button.primary` / `.secondary` / `.dashed` / `.small` | Une seule action principale par écran |
| Carte | `.card`, `.card.result` (cliquable), `.card.warning` | Regrouper une information |
| Champ | `components/Field.tsx`, `PasswordField`, `PhoneField` | Libellé toujours visible, aide sous le champ |
| Pastilles | `.chip` et `ServiceChips` | Choix rapides faciles à toucher |
| Onglets | `.segmented` (`AuthTabs`, `MethodSwitch`) | Deux ou trois choix exclusifs |
| En-tête violet | `components/PageHead.tsx` | Haut de chaque écran principal |
| Avatar | `components/Avatar.tsx` | Photo validée, sinon initiales |
| Score de confiance | `components/TrustScore.tsx` | Contrôles faits, sans promesse |
| Avis | `components/StarRating.tsx` | |
| Chiffres clés | `components/Stats.tsx` | |
| Favori | `components/FavoriteButton.tsx` | |
| Squelette | `components/Skeleton.tsx` | Forme du contenu pendant le chargement |

## Ajouter ou modifier un écran

1. Réutiliser un composant existant avant d'en créer un.
2. Utiliser uniquement les tokens : jamais `#…`, `rgba(…)` ou un espacement libre.
3. Écrire chaque texte en français **et** en anglais (`i18n/fr.ts`, `i18n/en.ts`).
   Le test de parité vérifie qu'aucune traduction ne manque.
4. Vérifier l'écran à 360 px, 768 px et 1440 px, puis au clavier (Tab), puis avec
   « réduire les animations ».
