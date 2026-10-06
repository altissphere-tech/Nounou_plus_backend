import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { applyToJob, getJob } from '../api/search'
import type { PublicJob } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import Avatar from '../components/Avatar'
import FavoriteButton from '../components/FavoriteButton'
import PageHead from '../components/PageHead'
import Stats from '../components/Stats'
import { RatingLine } from '../lists/cards'
import { money } from '../lists/format'
import { useMyProfile } from '../profile/useMyProfile'

/** Détail d'une annonce vue par un travailleur, avec « Répondre à l'annonce ». */
export default function JobDetail() {
  const { t, lang } = useI18n()
  const { user } = useAuth()
  const id = Number(useParams().id)
  const { data: me } = useMyProfile(user!.role)
  const [job, setJob] = useState<PublicJob | null | undefined>(undefined)
  const [result, setResult] = useState<{ ok: boolean; key: TranslationKey } | null>(null)
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
      setResult({ ok: true, key: mutual ? 'interest.mutual' : 'jobs.applied' })
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0
      const key = status === 403 ? 'jobs.notVerified' : status === 400 ? 'jobs.noProfile' : 'jobs.error'
      setResult({ ok: false, key })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack">
      <PageHead back={t('jobs.back')} overline={t('jobs.by', { name: job.client.name })} title={job.title}>
        <div className="head-row">
          <Avatar name={job.client.name} src={job.client.photo_url} size={56} />
          <span className="head-pill">{t(`service.${job.service.slug}`)}</span>
          <FavoriteButton kind="jobs" id={job.id} name={job.title} onDark />
        </div>
      </PageHead>
      <Stats
        items={[
          { label: t('jobs.budget'), value: job.budget ? money(job.budget, lang) : t('jobs.noBudget'), accent: true },
          { label: t('filters.availability'), value: t(`availability.${job.availability}`) },
          { label: t('filters.location'), value: job.location },
        ]}
      />
      <div className="card">
        {job.description && <p className="pre-line">{job.description}</p>}
        <p className="muted">{t('jobs.by', { name: job.client.name })}</p>
        <RatingLine rating={job.client.rating} />
        <Link to={`/signaler/${job.client.profile_id}`} state={{ name: job.client.name }} className="link report-link">
          ⚑ {t('report.link')}
        </Link>
      </div>

      <div className="card">
        <p className="muted">🔒 {t('worker.privacy')}</p>
        {blocker && !result && <div className="notice">{t(blocker)}</div>}
        {blocker === 'jobs.noProfile' && (
          <Link to="/profil" className="button secondary">
            {t('home.profile.create')}
          </Link>
        )}
        {result && <p className={result.ok ? 'info-banner' : 'error'} role="status">{t(result.key)}</p>}
        {!result?.ok && (
          <button type="button" className="button primary" onClick={apply} disabled={busy || Boolean(blocker)}>
            {busy ? t('common.loading') : t('jobs.apply')}
          </button>
        )}
      </div>
    </section>
  )
}
