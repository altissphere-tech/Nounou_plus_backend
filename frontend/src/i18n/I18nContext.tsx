import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import fr from './fr'
import type { TranslationKey } from './fr'
import { interpolate } from './interpolate'
import { DICTIONARIES, STORAGE_KEY, initialLanguage, loadLanguage } from './languages'
import type { Language } from './languages'

export type { Language } from './languages'

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
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Sans stockage, le choix vaut seulement pour cette visite
    }
    // Sans connexion, la langue déjà téléchargée reste affichée
    loadLanguage(next).then(
      () => setLangState(next),
      () => undefined,
    )
  }, [])

  const value = useMemo<I18nValue>(
    () => ({
      lang,
      setLang,
      // Tant que la langue choisie n'est pas téléchargée, le français s'affiche
      t: (key, params) => interpolate((DICTIONARIES[lang] ?? fr)[key], params),
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
