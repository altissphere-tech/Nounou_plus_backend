import LegalDocument from '../components/LegalDocument'
import { PRIVACY, PRIVACY_UPDATED } from '../content/legal'
import { useI18n } from '../i18n/I18nContext'

/** Politique de confidentialité (à faire valider par un juriste). */
export default function Privacy() {
  const { t, lang } = useI18n()
  return (
    <LegalDocument title={t('privacy.title')} updated={PRIVACY_UPDATED} sections={PRIVACY[lang]} path="/confidentialite" />
  )
}
