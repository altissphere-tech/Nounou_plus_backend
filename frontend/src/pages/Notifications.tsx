import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listNotifications, markNotificationsRead } from '../api/notifications'
import type { AppNotification } from '../api/types'
import PageHead from '../components/PageHead'
import { HelpCard, TipsCard } from '../components/SideCards'
import WithAside from '../components/WithAside'
import { useI18n } from '../i18n/I18nContext'
import { refreshNews } from '../matches/groups'
import { describe } from '../notifications/describe'
import { ListSkeleton } from '../components/Skeleton'

export default function Notifications() {
  const { t, lang } = useI18n()
  const [items, setItems] = useState<AppNotification[] | null | undefined>(undefined)

  useEffect(() => {
    listNotifications().then(
      (page) => {
        setItems(page.results)
        // Ouvrir la liste vaut lecture : la pastille de la cloche disparaît
        if (page.results.some((n) => !n.is_read)) markNotificationsRead().then(refreshNews, () => {})
      },
      () => setItems(null),
    )
  }, [])

  const date = (iso: string) =>
    new Date(iso).toLocaleString(lang === 'fr' ? 'fr-FR' : 'en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })

  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={t('notifications.title')} />
      <WithAside
        aside={
          <>
            <TipsCard />
            <HelpCard />
          </>
        }
      >
        {items === undefined && <ListSkeleton />}
        {items === null && <p className="error">{t('list.error')}</p>}
        {items?.length === 0 && <p className="card muted">{t('notifications.empty')}</p>}
        {items && items.length > 0 && (
          <ul className="notifications">
            {items.map((n) => {
              const { icon: Icon, text, to } = describe(n, t)
              return (
                <li key={n.id}>
                  <Link to={to} className={`notification ${n.is_read ? '' : 'unread'} kind-${n.kind}`}>
                    <span className="notification-icon" aria-hidden="true">
                      <Icon size={20} />
                    </span>
                    <span className="notification-text">
                      <span>{text}</span>
                      <span className="muted small-text">{date(n.created_at)}</span>
                    </span>
                    {!n.is_read && <span className="visually-hidden">{t('notifications.new')}</span>}
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </WithAside>
    </section>
  )
}
