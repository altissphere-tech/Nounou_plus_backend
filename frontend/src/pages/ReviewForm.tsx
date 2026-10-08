import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { listMatches } from '../api/matches'
import { CLIENT_CRITERIA, WORKER_CRITERIA, sendReview } from '../api/trust'
import type { Match } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import StarRating from '../components/StarRating'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import PageSkeleton from '../components/PageSkeleton'

/** Évaluation de l'autre personne d'une mise en relation, après la période d'essai. */
export default function ReviewForm() {
  const { t, lang } = useI18n()
  const { user } = useAuth()
  const navigate = useNavigate()
  const matchId = Number(useParams().id)
  const [match, setMatch] = useState<Match | null | undefined>(undefined)
  const [scores, setScores] = useState<Record<string, number>>({})
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    listMatches().then(
      (page) => setMatch(page.results.find((m) => m.id === matchId) ?? null),
      () => setMatch(null),
    )
  }, [matchId])

  if (match === undefined) return <PageSkeleton />
  if (match === null) return <p className="error">{t('matches.error')}</p>

  // Une famille note un travailleur, un travailleur note une famille
  const criteria = user!.role === 'client' ? WORKER_CRITERIA : CLIENT_CRITERIA
  const name = `${match.other_party.first_name} ${match.other_party.last_name}`

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (criteria.some((c) => !scores[c])) {
      setError(t('review.missing'))
      return
    }
    setBusy(true)
    setError('')
    try {
      await sendReview(matchId, scores, comment.trim())
      navigate('/relations', { state: { reviewed: true } })
    } catch (err) {
      setError(errorText(err, lang, t, 'review.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('review.title')}</h1>
      <p className="profile-name">{t('review.about', { name })}</p>
      <p className="muted">{t('review.intro')}</p>
      {criteria.map((criterion) => (
        <StarRating
          key={criterion}
          label={t(`criteria.${criterion}` as TranslationKey)}
          value={scores[criterion] ?? 0}
          onChange={(value) => {
            setError('')
            setScores((current) => ({ ...current, [criterion]: value }))
          }}
        />
      ))}
      <Field label={t('review.comment')}>
        <textarea
          rows={4}
          maxLength={1000}
          placeholder={t('review.comment.placeholder')}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </Field>
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : t('review.send')}
      </button>
      <Link to="/relations" className="link">
        {t('profile.cancel')}
      </Link>
    </form>
  )
}
