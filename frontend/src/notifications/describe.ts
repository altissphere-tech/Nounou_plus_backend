import type { LucideIcon } from 'lucide-react'
import { AlertTriangle, BadgeCheck, Camera, Heart, MessageCircle, Sparkles, Users } from 'lucide-react'
import type { AppNotification } from '../api/types'
import type { TranslationKey } from '../i18n/fr'

type Translate = (key: TranslationKey, values?: Record<string, string>) => string

/** Phrase, icône et écran à ouvrir pour chaque type de notification. */
export function describe(n: AppNotification, t: Translate): { icon: LucideIcon; text: string; to: string } {
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
