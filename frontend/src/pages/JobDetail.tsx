import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { applyToJob, getJob } from '../api/search'
import type { PublicJob } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { RatingLine } from '../lists/cards'
import { amount } from '../lists/format'
import { useMyProfile } from '../profile/useMyProfile'

/** Détail d'une annonce vue par un travailleur, avec « Répondre à l'annonce ». */
export default function JobDetail() {
  const { t } = useI18n()
  const { user } = useAuth()
  const navigate = useNavigate()
  const id = Number(useParams().id)
  const { data: me } = useMyProfile(user!.role)
  const [job, setJob] = useState<PublicJob | null | undefined>(undefined)
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getJob<PublicJob>(id).then(setJob, () => setJob(null))
  }, [id])

  if (job === undefined) return <p className="muted">{t('common.loading')}</p>
  if (job === null) {
    return (
      <div className="card">
        <p>{t('jobs.notFound')}</p>
        <Link to="/annonces" className="button secondary">
          {t('jobs.back')}
        </Link>
      </div>
    )
  }

  // Le travailleur doit avoir un profil vérifié pour répondre
  const profile = me?.kind === 'worker' ? me.profile : undefined
  const blocker = me === undefined ? null : !profile ? 'jobs.noProfile' : !profile.is_verified ? 'jobs.notVerified' : null

  async function apply() {
    setBusy(true)
    setResult(null)
    try {
      const response = await applyToJob(job!.id)
      const mutual = response.match.status === 'mutuel'
      setResult({ ok: true, text: t(mutual ? 'interest.mutual' : 'jobs.applied') })
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0
      const key = status === 403 ? 'jobs.notVerified' : status === 400 ? 'jobs.noProfile' : 'jobs.error'
      setResult({ ok: false, text: t(key) })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack">
      <button type="button" className="link back" onClick={() => navigate(-1)}>
        ← {t('jobs.back')}
      </button>
      <div className="card">
        <h1 className="profile-name">{job.title}</h1>
        <div className="tags">
          <span className="tag">{t(`service.${job.service.slug}`)}</span>
        </div>
        <dl className="details">
          <dt>{t('filters.location')}</dt>
          <dd>{job.location}</dd>
          <dt>{t('filters.availability')}</dt>
          <dd>{t(`availability.${job.availability}`)}</dd>
          <dt>{t('jobs.budget')}</dt>
          <dd>{job.budget ? t('home.profile.perMonth', { amount: amount(job.budget) }) : t('jobs.noBudget')}</dd>
        </dl>
        {job.description && <p className="pre-line">{job.description}</p>}
        <p className="muted">{t('jobs.by', { name: job.client.name })}</p>
        <RatingLine rating={job.client.rating} />
      </div>

      <div className="card">
        <p className="muted">🔒 {t('worker.privacy')}</p>
        {blocker && !result && <div className="notice">{t(blocker)}</div>}
        {blocker === 'jobs.noProfile' && (
          <Link to="/profil" className="button secondary">
            {t('home.profile.create')}
          </Link>
        )}
        {result && <p className={result.ok ? 'info-banner' : 'error'} role="status">{result.text}</p>}
        {!result?.ok && (
          <button type="button" className="button primary" onClick={apply} disabled={busy || Boolean(blocker)}>
            {busy ? t('common.loading') : t('jobs.apply')}
          </button>
        )}
      </div>
    </section>
  )
}
