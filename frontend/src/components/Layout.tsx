import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import BottomNav from './BottomNav'
import IdleGuard from './IdleGuard'
import Logo from './Logo'
import NotificationBell from './NotificationBell'
import OfflineBanner from './OfflineBanner'
import ScrollToTop from './ScrollToTop'

/**
 * Cadre commun à tous les écrans : en-tête (logo + langue), contenu, navigation.
 * Téléphone : barre de navigation en bas. Ordinateur (écran large) : menu à gauche
 * et contenu sur toute la largeur (voir « Grand écran » dans styles.css).
 */
export default function Layout({ children }: { children: ReactNode }) {
  const { lang, setLang, t } = useI18n()
  const { user } = useAuth()
  return (
    <div className={user ? 'app with-nav' : 'app'}>
      <ScrollToTop />
      <header className="header">
        <Link to="/" className="header-logo">
          <Logo size={22} />
        </Link>
        <div className="header-actions">
          <button
            type="button"
            className="lang-switch"
            onClick={() => setLang(lang === 'fr' ? 'en' : 'fr')}
          >
            {t('lang.switch')}
          </button>
          <NotificationBell />
        </div>
      </header>
      <OfflineBanner />
      <main className="content">{children}</main>
      <BottomNav />
      <IdleGuard />
    </div>
  )
}
