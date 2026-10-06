import { Link, useLocation } from 'react-router-dom'
import type { Me } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { amount } from '../lists/format'
import type { MyProfile } from '../profile/useMyProfile'
import { useMyProfile } from '../profile/useMyProfile'


function ProfileCard({ data }: { data: MyProfile }) {
  const { t } = useI18n()
  const isWorker = data.kind === 'worker'

  if (!data.profile) {
    return (
      <div className="card highlight">
        <h2>{t('home.next.title')}</h2>
        <p>{isWorker ? t('home.next.worker') : t('home.next.client')}</p>
        <Link to="/profil" className="button primary">
          {t('home.profile.create')}
        </Link>
      </div>
    )
  }

  const p = data.profile
  const rating = p.rating.average
    ? t('home.profile.rating', { average: p.rating.average, count: String(p.rating.count) })
    : t('home.profile.noRating')

  return (
    <div className="card">
      <h2>{t('home.profile.title')}</h2>
      <p className="profile-name">
        {p.first_name} {p.last_name}
      </p>
      <p className="muted">📍 {p.location}</p>
      <div className="tags">
        {p.services_list.map((slug) => (
          <span key={slug} className="tag">
            {t(`service.${slug}`)}
          </span>
        ))}
      </div>
      <dl className="details">
        {data.kind === 'worker' ? (
          <>
            <dt>{t('profile.availability.worker')}</dt>
            <dd>{t(`availability.${data.profile.availability}`)}</dd>
            <dt>{t('profile.experience')}</dt>
            <dd>{t('home.profile.years', { count: String(data.profile.years_experience) })}</dd>
            <dt>{t('profile.salary')}</dt>
            <dd>{t('home.profile.perMonth', { amount: amount(data.profile.expected_salary) })}</dd>
          </>
        ) : (
          <>
            <dt>{t('profile.availability.client')}</dt>
            <dd>{t(`availability.${data.profile.availability_needed}`)}</dd>
            {data.profile.budget !== null && (
              <>
                <dt>{t('profile.budget')}</dt>
                <dd>{t('home.profile.perMonth', { amount: amount(data.profile.budget) })}</dd>
              </>
            )}
          </>
        )}
      </dl>
      <p className="muted">⭐ {rating}</p>

      {data.kind === 'worker' &&
        (data.profile.is_verified ? (
          <div className="notice success">
            <strong>✔ {t('home.profile.verified')}</strong>
            <span>{t('home.profile.verified.note')}</span>
          </div>
        ) : (
          <div className="notice">
            <strong>{t('home.profile.notVerified')}</strong>
            <span>{t('home.profile.notVerified.note')}</span>
          </div>
        ))}

      <Link to="/profil" className="button secondary">
        {t('home.profile.edit')}
      </Link>
    </div>
  )
}

function AccountCard({ user, onLogout }: { user: Me; onLogout: () => void }) {
  const { t } = useI18n()
  return (
    <div className="card">
      <h2>{t('home.account')}</h2>
      <dl className="details">
        <dt>{t('home.phone')}</dt>
        <dd>{user.phone}</dd>
        <dt>{t('home.role')}</dt>
        <dd>{t(`home.role.${user.role}` as TranslationKey)}</dd>
      </dl>
      <button type="button" className="button secondary" onClick={onLogout}>
        {t('home.logout')}
      </button>
    </div>
  )
}

export default function Home() {
  const { t } = useI18n()
  const { user, logout } = useAuth()
  const saved = (useLocation().state as { saved?: boolean } | null)?.saved
  const { data, failed } = useMyProfile(user!.role)

  return (
    <section className="stack">
      <h1>{t('home.hello')}</h1>
      {saved && <p className="info-banner">✔ {t('profile.saved')}</p>}

      {user!.warnings.length > 0 && (
        <div className="card warning">
          <h2>{t('home.warnings')}</h2>
          {user!.warnings.map((w) => (
            <p key={w.date}>{w.message}</p>
          ))}
        </div>
      )}

      {failed && <p className="error">{t('profile.loadError')}</p>}
      {!data && !failed && <p className="muted">{t('common.loading')}</p>}
      {data && <ProfileCard data={data} />}

      <AccountCard user={user!} onLogout={logout} />
    </section>
  )
}
