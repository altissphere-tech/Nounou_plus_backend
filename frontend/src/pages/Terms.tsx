import LegalDocument from '../components/LegalDocument'
import { TERMS, TERMS_UPDATED } from '../content/terms'
import { useI18n } from '../i18n/I18nContext'

/** Conditions d'utilisation (brouillon à faire valider par un juriste). */
export default function Terms() {
  const { t, lang } = useI18n()
  return <LegalDocument title={t('terms.title')} updated={TERMS_UPDATED} sections={TERMS[lang]} path="/conditions" />
}
