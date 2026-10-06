import { ApiError } from '../api/client'
import type { Language } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'

/** Le serveur ne répond pas (alors qu'internet fonctionne) : message + rappel en développement. */
function serverDown(t: (key: TranslationKey) => string, dev: boolean): string {
  return dev ? `${t('common.serverDown')} ${t('common.serverDown.dev')}` : t('common.serverDown')
}

/**
 * Message d'erreur à afficher à l'utilisateur.
 * - Erreur de l'API (4xx) : en français, le message précis du serveur ; en anglais,
 *   un message traduit (les messages du serveur sont en français).
 * - Serveur en panne ou injoignable : « le serveur ne répond pas ».
 * - Téléphone sans internet : « vérifiez votre connexion internet ».
 */
export function errorText(
  error: unknown,
  lang: Language,
  t: (key: TranslationKey) => string,
  fallbackKey: TranslationKey,
  options: { online?: boolean; dev?: boolean } = {},
): string {
  const online = options.online ?? navigator.onLine
  const dev = options.dev ?? import.meta.env.DEV
  if (error instanceof ApiError) {
    if (error.status >= 500) {
      // 503 : service volontairement indisponible (ex : envoi des SMS), le serveur l'explique
      return lang === 'fr' && error.status === 503 && error.message ? error.message : serverDown(t, dev)
    }
    return lang === 'fr' && error.message ? error.message : t(fallbackKey)
  }
  return online ? serverDown(t, dev) : t('common.networkError')
}
