import { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { unreadNotifications } from '../api/notifications'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { onNewsRefresh } from '../matches/groups'

const REFRESH_EVERY_MS = 60000 // recompte toutes les minutes tant que l'application est ouverte

/** Cloche de l'en-tête, avec le nombre de notifications non lues. */
export default function NotificationBell() {
  const { user } = useAuth()
  const { t } = useI18n()
  const { pathname } = useLocation()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    if (!user) return
    let cancelled = false
    const load = () =>
      unreadNotifications().then(
        (data) => !cancelled && setUnread(data.unread),
        () => {},
      )
    load()
    const timer = window.setInterval(load, REFRESH_EVERY_MS)
    const unsubscribe = onNewsRefresh(load)
    return () => {
      cancelled = true
      window.clearInterval(timer)
      unsubscribe()
    }
  }, [user, pathname])

  if (!user) return null
  return (
    <Link
      to="/notifications"
      className="icon-button bell"
      aria-label={unread ? t('notifications.unread', { count: String(unread) }) : t('notifications.title')}
    >
      <Bell size={20} />
      {unread > 0 && <span className="badge-dot">{unread > 9 ? '9+' : unread}</span>}
    </Link>
  )
}
