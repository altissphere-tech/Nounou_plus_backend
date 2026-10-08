import fr from './fr'
import type { TranslationKey } from './fr'

export type Language = 'fr' | 'en'

type Dictionary = Record<TranslationKey, string>

/**
 * Le français est dans le fichier principal ; l'anglais n'est téléchargé que pour
 * les personnes qui le choisissent (moins de données à la première ouverture).
 */
export const DICTIONARIES: Partial<Record<Language, Dictionary>> = { fr }
export const STORAGE_KEY = 'nounou.lang'

export async function loadLanguage(lang: Language): Promise<void> {
  if (!DICTIONARIES[lang]) DICTIONARIES[lang] = (await import('./en')).default
}

export function initialLanguage(): Language {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'fr' || saved === 'en') return saved
  } catch {
    // Stockage indisponible (navigation privée) : on garde la valeur par défaut
  }
  return navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'fr'
}

