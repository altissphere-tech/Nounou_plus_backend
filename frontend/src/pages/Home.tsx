import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { money } from '../lists/format'
import Avatar from '../components/Avatar'
import PageHead from '../components/PageHead'
import TrustScore from '../components/TrustScore'
import InstallPrompt from '../pwa/InstallPrompt'
import type { MyProfile } from '../profile/useMyProfile'
import { useMyPhoto } from '../profile/useMyPhoto'
import { useMyProfile } from '../profile/useMyProfile'
import { ListSkeleton } from '../components/Skeleton'


function ProfileCard({ data }: { data: MyProfile }) {
  const { t, lang } = useI18n()
  const { user } = useAuth()
  const photo = useMyPhoto(user?.photo_status)
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
    <div className="card profile-card">
      <div className="col">
        <h2 className="overline">{t('home.profile.title')}</h2>
        <div className="person">
          <Avatar name={`${p.first_name} ${p.last_name}`} src={photo} size={56} />
          <div>
            <p className="profile-name">
              {p.first_name} {p.last_name}
            </p>
            <p className="muted">📍 {p.location}</p>
          </div>
        </div>
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
              <dt>{t('summary.salary')}</dt>
              <dd>{t('home.profile.perMonth', { amount: money(data.profile.expected_salary, lang) })}</dd>
            </>
          ) : (
            <>
              <dt>{t('profile.availability.client')}</dt>
              <dd>{t(`availability.${data.profile.availability_needed}`)}</dd>
              {data.profile.budget !== null && (
                <>
                  <dt>{t('jobs.budget')}</dt>
                  <dd>{t('home.profile.perMonth', { amount: money(data.profile.budget, lang) })}</dd>
                </>
              )}
            </>
          )}
        </dl>
        <p className="muted">⭐ {rating}</p>
        <Link to="/profil" className="button secondary">
          {t('home.profile.edit')}
        </Link>
        {data.kind === 'worker' && data.profile.is_verified && (
          <Link to="/documents" className="link">
            {t('home.profile.docs')}
          </Link>
        )}
      </div>
      {data.kind === 'worker' && (
        <div className="col">
          <TrustScore trust={data.profile.trust} />
          {!data.profile.is_verified && (
            <div className="notice">
              <strong>{t('home.profile.notVerified')}</strong>
              <span>{t('home.profile.notVerified.note')}</span>
              <Link to="/documents" className="button small primary">
                {t('home.profile.sendDocs')}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Home() {
  const { t } = useI18n()
  const { user } = useAuth()
  const saved = (useLocation().state as { saved?: boolean } | null)?.saved
  const { data, failed } = useMyProfile(user!.role)

  return (
    <section className="stack">
      {data?.profile ? (
        <PageHead overline={t('home.greeting')} title={`${data.profile.first_name} ${data.profile.last_name}`} />
      ) : (
        <PageHead title={t('home.hello')} />
      )}
      {saved && <p className="info-banner">✔ {t('profile.saved')}</p>}

      {user!.warnings.length > 0 && (
        <div className="card warning">
          <h2>{t('home.warnings')}</h2>
          {user!.warnings.map((w) => (
            <p key={w.date}>{w.message}</p>
          ))}
        </div>
      )}

      {user!.pending_email && (
        <Link to="/securite" className="notice email-notice">
          <strong>{t('home.confirmEmail')}</strong>
          <span>{t('home.confirmEmail.hint', { email: user!.pending_email })}</span>
        </Link>
      )}

      {failed && <p className="error">{t('profile.loadError')}</p>}
      {!data && !failed && <ListSkeleton count={1} />}
      {data && <ProfileCard data={data} />}
      <InstallPrompt />

    </section>
  )
}
