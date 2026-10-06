import { useEffect, useState } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Briefcase, ClipboardList, Heart, House, Search } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { listMatches } from '../api/matches'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { newsCount, onNewsRefresh } from '../matches/groups'

/**
 * Nombre de nouveautés (intérêts reçus + messages non lus), recompté à chaque
 * changement d'écran et après chaque action (accepter, refuser, lire).
 */
function useNews(enabled: boolean): number {
  const { pathname } = useLocation()
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    const load = () =>
      listMatches().then(
        (page) => !cancelled && setCount(newsCount(page.results)),
        () => {},
      )
    load()
    const unsubscribe = onNewsRefresh(load)
    return () => {
      cancelled = true
      unsubscribe()
    }
  }, [enabled, pathname])
  return enabled ? count : 0
}

/** Barre de navigation en bas de l'écran (utilisateurs connectés). */
export default function BottomNav() {
  const { user } = useAuth()
  const { t } = useI18n()
  const news = useNews(Boolean(user))
  if (!user) return null

  const items: { to: string; icon: LucideIcon; label: TranslationKey; badge?: number }[] =
    user.role === 'client'
      ? [
          { to: '/accueil', icon: House, label: 'nav.home' },
          { to: '/recherche', icon: Search, label: 'nav.search' },
          { to: '/mes-annonces', icon: ClipboardList, label: 'nav.myJobs' },
          { to: '/relations', icon: Heart, label: 'nav.matches', badge: news },
        ]
      : [
          { to: '/accueil', icon: House, label: 'nav.home' },
          { to: '/annonces', icon: Briefcase, label: 'nav.jobs' },
          { to: '/relations', icon: Heart, label: 'nav.matches', badge: news },
        ]

  return (
    <nav className="bottom-nav">
      {items.map((item) => (
        <NavLink key={item.to} to={item.to} className="bottom-nav-item">
          <span aria-hidden="true" className="bottom-nav-icon">
            <item.icon size={22} strokeWidth={2.2} />
            {item.badge ? <span className="badge-dot">{item.badge}</span> : null}
          </span>
          <span>{t(item.label)}</span>
        </NavLink>
      ))}
    </nav>
  )
}
