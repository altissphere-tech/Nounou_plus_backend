import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { AlertTriangle, BadgeCheck, Camera, Heart, MessageCircle, Sparkles, Users } from 'lucide-react'
import { listNotifications, markNotificationsRead } from '../api/notifications'
import type { AppNotification } from '../api/types'
import PageHead from '../components/PageHead'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { refreshNews } from '../matches/groups'
import { ListSkeleton } from '../components/Skeleton'

/** Phrase, icône et écran à ouvrir pour chaque type de notification. */
function describe(n: AppNotification, t: (key: TranslationKey, values?: Record<string, string>) => string) {
  const name = n.params.name ?? ''
  const approved = n.params.approved
  switch (n.kind) {
    case 'interest_received':
      return { icon: Heart, text: t('notif.interest', { name }), to: '/relations' }
    case 'match_mutual':
      return { icon: Sparkles, text: t('notif.match', { name }), to: `/relations/${n.params.match_id}` }
    case 'new_message':
      return {
        icon: MessageCircle,
        text: t(n.count > 1 ? 'notif.messages' : 'notif.message', { name, count: String(n.count) }),
        to: `/relations/${n.params.match_id}`,
      }
    case 'document_reviewed':
      return {
        icon: BadgeCheck,
        text: approved
          ? t('notif.docApproved', { doc: t(`docName.${n.params.doc_type ?? 'identite'}` as TranslationKey) })
          : t('notif.docRejected', { reason: n.params.reason ?? '' }),
        to: '/documents',
      }
    case 'photo_reviewed':
      return {
        icon: Camera,
        text: approved ? t('notif.photoApproved') : t('notif.photoRejected', { reason: n.params.reason ?? '' }),
        to: '/profil',
      }
    case 'reference_reviewed':
      return {
        icon: Users,
        text: t(approved ? 'notif.refApproved' : 'notif.refRejected', { name }),
        to: '/documents',
      }
    default:
      return { icon: AlertTriangle, text: t('notif.warning'), to: '/accueil' }
  }
}

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
      {items === undefined && <ListSkeleton />}
      {items === null && <p className="error">{t('list.error')}</p>}
      {items?.length === 0 && <p className="card muted">{t('notifications.empty')}</p>}
      {items && items.length > 0 && (
        <ul className="notifications">
          {items.map((n) => {
            const { icon: Icon, text, to } = describe(n, t) as { icon: LucideIcon; text: string; to: string }
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
    </section>
  )
}
