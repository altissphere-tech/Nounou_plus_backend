import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useI18n } from '../i18n/I18nContext'
import BottomNav from './BottomNav'
import Logo from './Logo'
import OfflineBanner from './OfflineBanner'
import ScrollToTop from './ScrollToTop'

/** Cadre commun à tous les écrans : en-tête (logo + langue) et contenu centré. */
export default function Layout({ children }: { children: ReactNode }) {
  const { lang, setLang, t } = useI18n()
  return (
    <div className="app">
      <ScrollToTop />
      <header className="header">
        <Link to="/" className="header-logo">
          <Logo size={22} />
        </Link>
        <button
          type="button"
          className="lang-switch"
          onClick={() => setLang(lang === 'fr' ? 'en' : 'fr')}
        >
          {t('lang.switch')}
        </button>
      </header>
      <OfflineBanner />
      <main className="content">{children}</main>
      <BottomNav />
    </div>
  )
}
