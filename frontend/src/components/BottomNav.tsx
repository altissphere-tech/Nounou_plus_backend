import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'

/** Barre de navigation en bas de l'écran (utilisateurs connectés). */
export default function BottomNav() {
  const { user } = useAuth()
  const { t } = useI18n()
  if (!user) return null

  const items: { to: string; icon: string; label: TranslationKey }[] =
    user.role === 'client'
      ? [
          { to: '/accueil', icon: '🏠', label: 'nav.home' },
          { to: '/recherche', icon: '🔍', label: 'nav.search' },
          { to: '/mes-annonces', icon: '📋', label: 'nav.myJobs' },
        ]
      : [
          { to: '/accueil', icon: '🏠', label: 'nav.home' },
          { to: '/annonces', icon: '📋', label: 'nav.jobs' },
        ]

  return (
    <nav className="bottom-nav">
      {items.map((item) => (
        <NavLink key={item.to} to={item.to} className="bottom-nav-item">
          <span aria-hidden="true">{item.icon}</span>
          <span>{t(item.label)}</span>
        </NavLink>
      ))}
    </nav>
  )
}
