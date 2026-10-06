import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { expressInterest, getWorker, getWorkerReviews } from '../api/search'
import type { PublicWorker, ReviewsPage } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { RatingLine } from '../lists/cards'
import { money } from '../lists/format'

/** Fiche d'un travailleur vue par une famille, avec le bouton « Je suis intéressé(e) ». */
export default function WorkerDetail() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
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
      <button type="button" className="link back" onClick={() => navigate(-1)}>
        ← {t('worker.back')}
      </button>

      <div className="card">
        <div className="result-head">
          <h1 className="profile-name">
            {worker.first_name} {worker.last_name}
          </h1>
          {worker.is_verified && <span className="verified">✔ {t('worker.verified')}</span>}
        </div>
        <div className="tags">
          {worker.services_list.map((slug) => (
            <span key={slug} className="tag">
              {t(`service.${slug}`)}
            </span>
          ))}
        </div>
        <dl className="details">
          <dt>{t('filters.location')}</dt>
          <dd>{worker.location}</dd>
          <dt>{t('filters.availability')}</dt>
          <dd>{t(`availability.${worker.availability}`)}</dd>
          <dt>{t('profile.experience')}</dt>
          <dd>{t('home.profile.years', { count: String(worker.years_experience) })}</dd>
          <dt>{t('summary.salary')}</dt>
          <dd>{t('home.profile.perMonth', { amount: money(worker.expected_salary, lang) })}</dd>
        </dl>
        <RatingLine rating={worker.rating} />
        {worker.bio && (
          <>
            <h2>{t('worker.about')}</h2>
            <p className="pre-line">{worker.bio}</p>
          </>
        )}
        <p className="field-hint">{t('worker.verifiedNote')}</p>
      </div>

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
        <h2>{t('worker.reviews')}</h2>
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
    </section>
  )
}
