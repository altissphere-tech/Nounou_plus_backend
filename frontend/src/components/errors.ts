import { ApiError } from '../api/client'
import type { Language } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'

/**
 * Message d'erreur à afficher à l'utilisateur.
 * Les messages de l'API sont en français : on les affiche tels quels en français,
 * et on utilise un message traduit en anglais.
 */
export function errorText(
  error: unknown,
  lang: Language,
  t: (key: TranslationKey) => string,
  fallbackKey: TranslationKey,
): string {
  if (error instanceof ApiError) {
    return lang === 'fr' && error.status < 500 && error.message ? error.message : t(fallbackKey)
  }
  return t('common.networkError')
}
