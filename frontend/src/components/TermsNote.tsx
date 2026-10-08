import { Link } from 'react-router-dom'
import { useI18n } from '../i18n/I18nContext'

/** « En continuant, vous acceptez les conditions d'utilisation et la politique de confidentialité. » */
export default function TermsNote() {
  const { t } = useI18n()
  return (
    <p className="terms-note">
      {t('terms.note')}{' '}
      <Link to="/conditions">{t('terms.link')}</Link> {t('terms.and')}{' '}
      <Link to="/confidentialite">{t('privacy.link')}</Link>.
    </p>
  )
}
