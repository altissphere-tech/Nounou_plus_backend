import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { BadgeCheck, Bell, ChevronRight, FileText, Heart, LifeBuoy, Lock, LogOut, Scale, ShieldCheck, UserPen } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import Avatar from '../components/Avatar'
import PageHead from '../components/PageHead'
import { HelpCard, ProfilePreviewCard, ProgressCard, RecentActivityCard } from '../components/SideCards'
import WithAside from '../components/WithAside'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { useMyPhoto } from '../profile/useMyPhoto'
import { useMyProfile } from '../profile/useMyProfile'

const VERSION = 'v1.0.0'

/** Écran « Mon compte » (onglet Profil) : menu vers les réglages, l'aide et la déconnexion. */
export default function Account() {
  const { t } = useI18n()
  const { user, logout } = useAuth()
  const { data } = useMyProfile(user!.role)
  const photo = useMyPhoto(user!.photo_status)
  const name = data?.profile ? `${data.profile.first_name} ${data.profile.last_name}` : user!.phone

  const items: { to: string; icon: LucideIcon; label: TranslationKey; hint?: string }[] = [
    { to: '/profil', icon: UserPen, label: data?.profile ? 'home.profile.edit' : 'home.profile.create' },
    ...(user!.role === 'travailleur'
      ? [{ to: '/documents', icon: BadgeCheck, label: 'account.verification' as TranslationKey }]
      : []),
    { to: '/favoris', icon: Heart, label: 'favorites.title' },
    { to: '/notifications', icon: Bell, label: 'notifications.title' },
    { to: '/securite', icon: ShieldCheck, label: 'security.title' },
    { to: '/aide', icon: LifeBuoy, label: 'help.title' },
    { to: '/conditions', icon: FileText, label: 'terms.title' },
    { to: '/confidentialite', icon: Lock, label: 'privacy.title' },
    { to: '/mentions-legales', icon: Scale, label: 'legal.title' },
  ]

  return (
    <section className="stack">
      <PageHead title={t('account.title')}>
        <div className="person">
          <Avatar name={name} src={photo} size={64} />
          <div className="person-text">
            <span className="profile-name">{name}</span>
            <span>{user!.phone}</span>
            <span>{t(`home.role.${user!.role}` as TranslationKey)}</span>
          </div>
        </div>
      </PageHead>

      <WithAside
        aside={
          <>
            <ProfilePreviewCard data={data} />
            <ProgressCard data={data} />
            <RecentActivityCard />
            <HelpCard />
          </>
        }
      >
        {user!.warnings.length > 0 && <p className="notice">{t('account.hasWarnings')}</p>}

        <ul className="menu">
          {items.map((item) => (
            <li key={item.to}>
              <Link to={item.to} className="menu-item">
                <span className="menu-icon" aria-hidden="true">
                  <item.icon size={20} />
                </span>
                <span className="menu-label">{t(item.label)}</span>
                <ChevronRight size={18} aria-hidden="true" className="menu-chevron" />
              </Link>
            </li>
          ))}
        </ul>

        <div className="card version">
          <span className="overline">{t('account.version')}</span>
          <span>NOUNOU+ {VERSION} · Lubumbashi</span>
        </div>

        <button type="button" className="button danger-outline" onClick={logout}>
          <LogOut size={18} aria-hidden="true" /> {t('home.logout')}
        </button>
      </WithAside>
    </section>
  )
}
