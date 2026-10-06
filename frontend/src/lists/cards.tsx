import { Link } from 'react-router-dom'
import type { MyJob, PublicJob, PublicWorker, Rating } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import { money } from './format'

export function RatingLine({ rating }: { rating: Rating }) {
  const { t } = useI18n()
  return (
    <span className="rating">
      ⭐{' '}
      {rating.average
        ? t('home.profile.rating', { average: rating.average, count: String(rating.count) })
        : t('home.profile.noRating')}
    </span>
  )
}

/** Carte d'un travailleur dans les résultats de recherche. */
export function WorkerCard({ worker }: { worker: PublicWorker }) {
  const { t, lang } = useI18n()
  return (
    <Link to={`/travailleurs/${worker.id}`} className="card result">
      <div className="result-head">
        <span className="profile-name">
          {worker.first_name} {worker.last_name}
        </span>
        {worker.is_verified && <span className="verified">✔ {t('worker.verified')}</span>}
      </div>
      <div className="tags">
        {worker.services_list.map((slug) => (
          <span key={slug} className="tag">
            {t(`service.${slug}`)}
          </span>
        ))}
      </div>
      <p className="muted">
        📍 {worker.location} · {t(`availability.${worker.availability}`)}
      </p>
      <p className="result-foot">
        <strong>{t('home.profile.perMonth', { amount: money(worker.expected_salary, lang) })}</strong>
        <span className="muted">{t('worker.experience', { count: String(worker.years_experience) })}</span>
      </p>
      <RatingLine rating={worker.rating} />
    </Link>
  )
}

/** Carte d'une annonce vue par un travailleur. */
export function JobCard({ job }: { job: PublicJob }) {
  const { t, lang } = useI18n()
  return (
    <Link to={`/annonces/${job.id}`} className="card result">
      <span className="profile-name">{job.title}</span>
      <div className="tags">
        <span className="tag">{t(`service.${job.service.slug}`)}</span>
      </div>
      <p className="muted">
        📍 {job.location} · {t(`availability.${job.availability}`)}
      </p>
      <p className="result-foot">
        <strong>
          {job.budget ? t('home.profile.perMonth', { amount: money(job.budget, lang) }) : t('jobs.noBudget')}
        </strong>
        <span className="muted">{t('jobs.by', { name: job.client.name })}</span>
      </p>
    </Link>
  )
}

/** Carte d'une annonce dans « Mes annonces » (famille), avec ses actions. */
export function MyJobCard({
  job,
  onStatus,
}: {
  job: MyJob
  onStatus: (status: MyJob['status']) => void
}) {
  const { t, lang } = useI18n()
  return (
    <div className="card">
      <div className="result-head">
        <span className="profile-name">{job.title}</span>
        <span className={`status status-${job.status}`}>{t(`jobStatus.${job.status}`)}</span>
      </div>
      <div className="tags">
        <span className="tag">{t(`service.${job.service.slug}`)}</span>
      </div>
      <p className="muted">
        📍 {job.location} · {t(`availability.${job.availability}`)}
        {job.budget && ` · ${t('home.profile.perMonth', { amount: money(job.budget, lang) })}`}
      </p>
      <p>
        <strong>{t('myJobs.responses', { count: String(job.interested_workers) })}</strong>
      </p>
      <div className="actions">
        <Link to={`/mes-annonces/${job.id}`} className="button small secondary">
          {t('myJobs.edit')}
        </Link>
        {job.status === 'ouverte' ? (
          <>
            <button type="button" className="button small secondary" onClick={() => onStatus('pourvue')}>
              {t('myJobs.markFilled')}
            </button>
            <button type="button" className="button small secondary" onClick={() => onStatus('fermee')}>
              {t('myJobs.close')}
            </button>
          </>
        ) : (
          <button type="button" className="button small secondary" onClick={() => onStatus('ouverte')}>
            {t('myJobs.reopen')}
          </button>
        )}
      </div>
    </div>
  )
}
