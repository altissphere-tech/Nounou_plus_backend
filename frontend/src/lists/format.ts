import type { Language } from '../i18n/I18nContext'

/**
 * Montant en francs congolais, lisible : « 250 000 FC » (français) ou
 * « 250,000 FC » (anglais). Les centimes ne sont pas affichés.
 */
export function money(value: string | number, lang: Language): string {
  const formatted = new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', {
    maximumFractionDigits: 0,
  }).format(Number(value))
  return `${formatted} FC`
}
