import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { expressInterest, getWorker, getWorkerReviews } from '../api/search'
import type { PublicWorker, ReviewsPage } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import Avatar from '../components/Avatar'
import FavoriteButton from '../components/FavoriteButton'
import PageHead from '../components/PageHead'
import Stats from '../components/Stats'
import TrustScore from '../components/TrustScore'
import { money } from '../lists/format'

/** Fiche d'un travailleur vue par une famille, avec le bouton « Je suis intéressé(e) ». */
export default function WorkerDetail() {
  const { t, lang } = useI18n()
  const id = Number(useParams().id)
  const [worker, setWorker] = useState<PublicWorker | null | undefined>(undefined)
  const [reviews, setReviews] = useState<ReviewsPage | null>(null)
  const [result, setResult] = useState<{ ok: boolean; key: TranslationKey; noProfile?: boolean } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getWorker(id).then(setWorker, () => setWorker(null))
    getWorkerReviews(id).then(setReviews, () => setReviews(null))
  }, [id])

  if (worker === undefined) return <p className="muted">{t('common.loading')}</p>
  if (worker === null) {
    return (
      <div className="card">
        <p>{t('worker.notFound')}</p>
        <Link to="/recherche" className="button secondary">
          {t('worker.back')}
        </Link>
      </div>
    )
  }

  async function interest() {
    setBusy(true)
    setResult(null)
    try {
      const response = await expressInterest(worker!.id)
      const mutual = response.match.status === 'mutuel'
      setResult({ ok: true, key: mutual ? 'interest.mutual' : 'interest.sent' })
    } catch (err) {
      const noProfile = err instanceof ApiError && err.status === 400
      setResult({ ok: false, noProfile, key: noProfile ? 'interest.noProfile' : 'interest.error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack">
      <PageHead back={t('worker.back')} overline={worker.services_list.map((slug) => t(`search.short.${slug}`)).join(' · ')} title={`${worker.first_name} ${worker.last_name}`}>
        <div className="head-row">
          <Avatar name={`${worker.first_name} ${worker.last_name}`} src={worker.photo_url} size={64} />
          <span className="head-pill">{t(`availability.${worker.availability}`)}</span>
          <FavoriteButton kind="workers" id={worker.id} name={`${worker.first_name} ${worker.last_name}`} onDark />
        </div>
      </PageHead>
      <div className="detail-grid">
        <div className="col">
          <Stats
            items={[
              { label: t('stats.experience'), value: t('stats.years', { count: String(worker.years_experience) }) },
              { label: t('stats.salary'), value: money(worker.expected_salary, lang), accent: true },
              { label: t('stats.rating'), value: worker.rating.average ? `${worker.rating.average} ★` : '—' },
            ]}
          />

          <div className="card">
            <TrustScore trust={worker.trust} />
          </div>

          <div className="card">
            <h2 className="overline">{t('filters.location')}</h2>
            <p>📍 {worker.location}</p>
            <h2 className="overline">{t('filters.service')}</h2>
            <div className="tags">
              {worker.services_list.map((slug) => (
                <span key={slug} className="tag">
                  {t(`service.${slug}`)}
                </span>
              ))}
            </div>
            {worker.bio && (
              <>
                <h2 className="overline">{t('worker.about')}</h2>
                <p className="pre-line">{worker.bio}</p>
              </>
            )}
            <Link
              to={`/signaler/${worker.id}`}
              state={{ name: `${worker.first_name} ${worker.last_name}` }}
              className="link report-link"
            >
              ⚑ {t('report.link')}
            </Link>
          </div>
        </div>
        <aside className="col">
          <div className="card">
            <p className="muted">🔒 {t('worker.privacy')}</p>
            {result && <p className={result.ok ? 'info-banner' : 'error'} role="status">{t(result.key)}</p>}
            {!result?.ok && (
              <button type="button" className="button primary" onClick={interest} disabled={busy}>
                {busy ? t('common.loading') : t('interest.button')}
              </button>
            )}
            {result?.noProfile && (
              <Link to="/profil" className="button secondary">
                {t('home.profile.create')}
              </Link>
            )}
          </div>

          <div className="card">
            <h2 className="overline">{t('worker.reviews')}</h2>
            {!reviews || reviews.count === 0 ? (
              <p className="muted">{t('worker.noReviews')}</p>
            ) : (
              <>
                <dl className="details">
                  {Object.entries(reviews.summary.criteria).map(([name, value]) => (
                    <div key={name} className="contents">
                      <dt>{t(`criteria.${name}` as TranslationKey)}</dt>
                      <dd>{value ?? '—'}/5</dd>
                    </div>
                  ))}
                </dl>
                {reviews.results.map((review) => (
                  <div key={review.id} className="review">
                    <strong>
                      ⭐ {review.overall}/5 · {review.author_name}
                    </strong>
                    {review.comment && <p className="pre-line">{review.comment}</p>}
                  </div>
                ))}
              </>
            )}
          </div>
        </aside>
      </div>
    </section>
  )
}
