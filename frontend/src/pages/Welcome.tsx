import { Link } from 'react-router-dom'
import Logo from '../components/Logo'
import { useI18n } from '../i18n/I18nContext'

export default function Welcome() {
  const { t } = useI18n()
  return (
    <section className="welcome">
      <Logo size={44} />
      <p className="tagline">{t('app.tagline')}</p>
      <h1>{t('welcome.title')}</h1>
      <p className="muted">{t('welcome.intro')}</p>
      <div className="stack">
        <Link to="/inscription" className="button primary">
          {t('welcome.register')}
        </Link>
        <Link to="/connexion" className="button secondary">
          {t('welcome.login')}
        </Link>
      </div>
    </section>
  )
}
