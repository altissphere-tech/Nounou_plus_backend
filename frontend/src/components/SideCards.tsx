import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, CheckCircle2, Clock, MessageCircle, Phone } from 'lucide-react'
import { listNotifications } from '../api/notifications'
import type { AppNotification } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { CONTACT, CONTACT_PHONE_DIGITS } from '../content/contact'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { describe } from '../notifications/describe'
import type { MyProfile } from '../profile/useMyProfile'
import { useMyPhoto } from '../profile/useMyPhoto'
import { useMyProfile } from '../profile/useMyProfile'
import Avatar from './Avatar'

/*
 * Cartes de la colonne de droite (grand écran uniquement, voir WithAside).
 * Elles ne montrent que des informations que l'application affiche déjà ailleurs,
 * et respectent les mêmes règles : nom complet et téléphone jamais montrés comme
 * « vus par les autres », badge « Vérifié » jamais présenté comme une garantie.
 */

/** « Mon profil vu par les autres » : prénom + initiale, quartier, services, photo validée. */
export function ProfilePreviewCard({ data }: { data: MyProfile | undefined }) {
  const { t } = useI18n()
  const { user } = useAuth()
  const ownPhoto = useMyPhoto(user!.photo_status)
  if (!data) return null
  const p = data.profile
  const isWorker = data.kind === 'worker'
  if (!p) {
    return (
      <div className="card side-card">
        <h2>{t('aside.preview.title')}</h2>
        <p className="muted">{t('aside.preview.none')}</p>
        <Link to="/profil" className="button small primary">
          {t('home.profile.create')}
        </Link>
      </div>
    )
  }
  // Ce que voient les autres : seulement une photo validée par l'équipe
  const photo = user!.photo_status === 'validee' ? ownPhoto : null
  const shortName = `${p.first_name} ${p.last_name.charAt(0).toUpperCase()}.`
  const rating = p.rating.average
    ? t('home.profile.rating', { average: p.rating.average, count: String(p.rating.count) })
    : t('home.profile.noRating')
  const verified = data.kind === 'worker' && data.profile?.is_verified
  return (
    <div className="card side-card">
      <h2>{t('aside.preview.title')}</h2>
      <div className="person">
        <Avatar name={shortName} src={photo} size={52} />
        <div>
          <p className="profile-name">{shortName}</p>
          <p className="muted">📍 {p.location}</p>
        </div>
      </div>
      <div className="tags">
        {p.services_list.map((slug) => (
          <span key={slug} className="tag">
            {t(`service.${slug}` as TranslationKey)}
          </span>
        ))}
      </div>
      <p className="muted small-text">
        ⭐ {rating}
        {verified && <span className="verified">✔ {t('worker.verified')}</span>}
      </p>
      {verified && <p className="muted small-text">{t('worker.verifiedNote')}</p>}
      {user!.photo_status === 'en_attente' && <p className="muted small-text">{t('aside.preview.photoPending')}</p>}
      <p className="side-note">
        {isWorker && !verified ? t('aside.preview.hiddenWorker') : t(isWorker ? 'aside.preview.worker' : 'aside.preview.client')}
      </p>
      <Link to="/profil" className="button small secondary">
        {t('home.profile.edit')}
      </Link>
    </div>
  )
}

/** « Avancement » : les étapes déjà prévues par l'application (téléphone, profil, photo, contrôles). */
export function ProgressCard({ data }: { data: MyProfile | undefined }) {
  const { t } = useI18n()
  const { user } = useAuth()
  if (!data) return null
  const photo = user!.photo_status === 'validee'
  const steps: { key: TranslationKey; done: boolean }[] =
    data.kind === 'worker'
      ? [
          { key: 'trust.phone', done: user!.phone_verified },
          { key: 'aside.progress.profile', done: !!data.profile },
          { key: 'aside.progress.photo', done: photo },
          { key: 'trust.identity', done: !!data.profile?.trust.identity },
          { key: 'trust.references', done: !!data.profile?.trust.references },
        ]
      : [
          { key: 'trust.phone', done: user!.phone_verified },
          { key: 'aside.progress.profile', done: !!data.profile },
          { key: 'aside.progress.photo', done: photo },
          { key: 'aside.progress.email', done: user!.email_verified },
        ]
  const done = steps.filter((s) => s.done).length
  // Prochaine étape utile : créer le profil, sinon (travailleur) envoyer ses documents
  const next = !data.profile ? '/profil' : data.kind === 'worker' && done < steps.length ? '/documents' : null
  return (
    <div className="card side-card">
      <h2>
        {t('aside.progress.title')}
        <span className="side-count">{t('aside.progress.count', { done: String(done), total: String(steps.length) })}</span>
      </h2>
      <div
        className="side-progress"
        role="progressbar"
        aria-label={t('aside.progress.title')}
        aria-valuemin={0}
        aria-valuemax={steps.length}
        aria-valuenow={done}
      >
        <span style={{ width: `${(done / steps.length) * 100}%` }} />
      </div>
      <ul className="trust-steps side-steps">
        {steps.map((step) => (
          <li key={step.key} className={step.done ? 'done' : ''}>
            <span className="trust-dot">{step.done ? <Check size={16} strokeWidth={3} /> : <Clock size={16} />}</span>
            {t(step.key)}
            <span className="visually-hidden">{step.done ? t('trust.done') : t('trust.notYet')}</span>
          </li>
        ))}
      </ul>
      {next && (
        <Link to={next} className="button small primary">
          {t('aside.progress.complete')}
        </Link>
      )}
    </div>
  )
}

/** « Activité récente » : les 3 dernières notifications (sans les marquer comme lues). */
export function RecentActivityCard() {
  const { t, lang } = useI18n()
  const [items, setItems] = useState<AppNotification[] | null>(null)
  useEffect(() => {
    let cancelled = false
    listNotifications().then(
      (page) => !cancelled && setItems(page.results.slice(0, 3)),
      () => {},
    )
    return () => {
      cancelled = true
    }
  }, [])
  if (items === null) return null
  const date = (iso: string) =>
    new Date(iso).toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'short' })
  return (
    <div className="card side-card">
      <h2>{t('aside.activity.title')}</h2>
      {items.length === 0 ? (
        <p className="muted">{t('notifications.empty')}</p>
      ) : (
        <ul className="side-activity">
          {items.map((n) => {
            const { icon: Icon, text, to } = describe(n, t)
            return (
              <li key={n.id}>
                <Link to={to} className={n.is_read ? '' : 'unread'}>
                  <Icon size={18} aria-hidden="true" />
                  <span>{text}</span>
                  <span className="muted small-text">{date(n.created_at)}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
      <Link to="/notifications" className="link">
        {t('aside.activity.all')}
      </Link>
    </div>
  )
}

/** « Besoin d'aide ? » : contacts du support (les mêmes que l'écran Aide). */
export function HelpCard() {
  const { t, lang } = useI18n()
  return (
    <div className="card side-card">
      <h2>{t('aside.help.title')}</h2>
      <div className="side-actions">
        <a href={`https://wa.me/${CONTACT_PHONE_DIGITS}`} target="_blank" rel="noopener noreferrer" className="button small primary">
          <MessageCircle size={16} aria-hidden="true" /> WhatsApp
        </a>
        <a href={`tel:+${CONTACT_PHONE_DIGITS}`} className="button small secondary">
          <Phone size={16} aria-hidden="true" /> {t('aside.help.call')}
        </a>
      </div>
      <p className="muted small-text">
        {CONTACT.hours[lang]} · {CONTACT.phone}
      </p>
      <Link to="/aide" className="link">
        {t('help.title')}
      </Link>
    </div>
  )
}

const TIPS: TranslationKey[] = ['security.tip1', 'security.tip2', 'security.tip5']

/** Trois conseils de sécurité (les mêmes que l'écran Sécurité). */
export function TipsCard() {
  const { t } = useI18n()
  return (
    <div className="card side-card">
      <h2>{t('security.tips')}</h2>
      <ul className="tips">
        {TIPS.map((key) => (
          <li key={key}>
            <CheckCircle2 size={18} aria-hidden="true" /> {t(key)}
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Variantes qui chargent elles-mêmes le profil : le chargement n'a lieu que sur grand écran. */
export function MyProfilePreviewCard() {
  const { user } = useAuth()
  return <ProfilePreviewCard data={useMyProfile(user!.role).data} />
}

export function MyProgressCard() {
  const { user } = useAuth()
  return <ProgressCard data={useMyProfile(user!.role).data} />
}
