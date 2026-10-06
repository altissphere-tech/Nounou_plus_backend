import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import en from './en'
import fr from './fr'
import type { TranslationKey } from './fr'
import { interpolate } from './interpolate'

export type Language = 'fr' | 'en'

const DICTIONARIES: Record<Language, Record<TranslationKey, string>> = { fr, en }
const STORAGE_KEY = 'nounou.lang'

function initialLanguage(): Language {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'fr' || saved === 'en') return saved
  } catch {
    // Stockage indisponible (navigation privée) : on garde la valeur par défaut
  }
  return navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'fr'
}

interface I18nValue {
  lang: Language
  setLang: (lang: Language) => void
  t: (key: TranslationKey, params?: Record<string, string>) => string
}

const I18nContext = createContext<I18nValue | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(initialLanguage)

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const setLang = useCallback((next: Language) => {
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Sans stockage, le choix vaut seulement pour cette visite
    }
  }, [])

  const value = useMemo<I18nValue>(
    () => ({
      lang,
      setLang,
      t: (key, params) => interpolate(DICTIONARIES[lang][key], params),
    }),
    [lang, setLang],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext)
  if (!value) throw new Error('useI18n doit être utilisé dans <I18nProvider>')
  return value
}
