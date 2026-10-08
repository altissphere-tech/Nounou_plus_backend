import LegalDocument from '../components/LegalDocument'
import { LEGAL_NOTICE, LEGAL_UPDATED } from '../content/legal'
import { useI18n } from '../i18n/I18nContext'

/** Mentions légales : éditeur, rôle de la plateforme, propriété intellectuelle, hébergement. */
export default function LegalNotice() {
  const { t, lang } = useI18n()
  return (
    <LegalDocument title={t('legal.title')} updated={LEGAL_UPDATED} sections={LEGAL_NOTICE[lang]} path="/mentions-legales" />
  )
}
