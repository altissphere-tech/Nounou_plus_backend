import { Link } from 'react-router-dom'
import { MessageCircleHeart, Search, ShieldCheck } from 'lucide-react'
import Logo from '../components/Logo'
import { useI18n } from '../i18n/I18nContext'
import InstallPrompt from '../pwa/InstallPrompt'

const FEATURES = [
  { icon: Search, title: 'welcome.f1.title', text: 'welcome.f1.text' },
  { icon: ShieldCheck, title: 'welcome.f2.title', text: 'welcome.f2.text' },
  { icon: MessageCircleHeart, title: 'welcome.f3.title', text: 'welcome.f3.text' },
] as const

export default function Welcome() {
  const { t } = useI18n()
  return (
    <section className="welcome">
      <div className="welcome-hero">
        <Logo size={88} />
        <p className="motto">{t('brand.motto')}</p>
        <p className="tagline">{t('app.tagline')}</p>
      </div>
      <h1>{t('welcome.title')}</h1>
      <p className="muted">{t('welcome.intro')}</p>
      <div className="stack">
        <Link to="/inscription" className="button primary">
          {t('welcome.register')}
        </Link>
        <Link to="/connexion" className="button secondary">
          {t('welcome.login')}
        </Link>
        <InstallPrompt />
      </div>
      <h2 className="welcome-why">{t('welcome.why')}</h2>
      <ul className="features">
        {FEATURES.map((feature) => (
          <li key={feature.title} className="feature">
            <span className="feature-icon" aria-hidden="true">
              <feature.icon size={22} />
            </span>
            <span>
              <strong>{t(feature.title)}</strong>
              <span className="muted">{t(feature.text)}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
