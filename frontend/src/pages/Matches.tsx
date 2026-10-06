import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { acceptMatch, declineMatch, listMatches } from '../api/matches'
import type { Match } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { RatingLine } from '../lists/cards'
import type { TranslationKey } from '../i18n/fr'
import { groupMatches, refreshNews } from '../matches/groups'

function PartyName({ match }: { match: Match }) {
  const { first_name, last_name } = match.other_party
  return (
    <span className="profile-name">
      {first_name} {last_name}
    </span>
  )
}

/** Lien « Signaler ce profil » (le nom est transmis pour l'afficher sur le formulaire). */
function ReportLink({ match }: { match: Match }) {
  const { t } = useI18n()
  const name = `${match.other_party.first_name} ${match.other_party.last_name}`
  return (
    <Link to={`/signaler/${match.other_party.id}`} state={{ name }} className="link report-link">
      ⚑ {t('report.link')}
    </Link>
  )
}

/** Avis : bouton si possible, sinon date à partir de laquelle il le sera. */
function ReviewAction({ match, now }: { match: Match; now: number }) {
  const { t, lang } = useI18n()
  if (match.can_review) {
    return (
      <Link to={`/relations/${match.id}/avis`} className="button small secondary">
        ⭐ {t('review.button')}
      </Link>
    )
  }
  if (match.review_available_at && new Date(match.review_available_at).getTime() > now) {
    const date = new Date(match.review_available_at).toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB')
    return <p className="muted small-text">⭐ {t('review.availableOn', { date })}</p>
  }
  return null
}

function MatchCard({ match, now, children }: { match: Match; now: number; children?: ReactNode }) {
  const { t } = useI18n()
  return (
    <div className="card match-card">
      <div className="result-head">
        <PartyName match={match} />
        {match.unread_count > 0 && <span className="unread">{match.unread_count}</span>}
      </div>
      {match.job && <p className="muted">📋 {t('matches.job', { title: match.job.title })}</p>}
      <div className="tags">
        {match.other_party.services_list.map((slug) => (
          <span key={slug} className="tag">
            {t(`service.${slug}`)}
          </span>
        ))}
      </div>
      <p className="muted">📍 {match.other_party.location}</p>
      <RatingLine rating={match.other_party.rating} />
      {children}
      <ReviewAction match={match} now={now} />
      <ReportLink match={match} />
    </div>
  )
}

/** Intérêts reçus et envoyés, matchs (coordonnées) et accès à la messagerie. */
export default function Matches() {
  const { t } = useI18n()
  const { user } = useAuth()
  const [matches, setMatches] = useState<Match[] | null | undefined>(undefined)
  const [version, setVersion] = useState(0)
  const [now] = useState(() => Date.now()) // heure de référence pour les dates d'avis
  const reviewed = (useLocation().state as { reviewed?: boolean } | null)?.reviewed
  const [feedback, setFeedback] = useState<{ ok: boolean; key: TranslationKey } | null>(
    reviewed ? { ok: true, key: 'review.sent' } : null,
  )

  useEffect(() => {
    listMatches().then((page) => setMatches(page.results), () => setMatches(null))
    refreshNews()
  }, [version])

  if (matches === undefined) return <p className="muted">{t('common.loading')}</p>
  if (matches === null) return <p className="error">{t('list.error')}</p>

  const groups = groupMatches(matches)

  async function accept(match: Match) {
    setFeedback(null)
    try {
      const response = await acceptMatch(match)
      setFeedback({ ok: true, key: response.match.status === 'mutuel' ? 'matches.accepted' : 'interest.sent' })
      setVersion((v) => v + 1)
    } catch {
      setFeedback({ ok: false, key: 'matches.error' })
    }
  }

  async function decline(match: Match) {
    if (!window.confirm(t('matches.decline.confirm'))) return
    setFeedback(null)
    try {
      await declineMatch(match.id)
      setVersion((v) => v + 1)
    } catch {
      setFeedback({ ok: false, key: 'matches.error' })
    }
  }

  return (
    <section className="stack">
      <h1>{t('matches.title')}</h1>
      {feedback && <p className={feedback.ok ? 'info-banner' : 'error'} role="status">{t(feedback.key)}</p>}

      {matches.length === 0 && (
        <div className="card">
          <p>{t('matches.empty')}</p>
          <p className="muted">{user!.role === 'client' ? t('matches.empty.client') : t('matches.empty.worker')}</p>
          <Link to={user!.role === 'client' ? '/recherche' : '/annonces'} className="button primary">
            {user!.role === 'client' ? t('nav.search') : t('nav.jobs')}
          </Link>
        </div>
      )}

      {groups.incoming.length > 0 && (
        <>
          <h2 className="section-title">
            {t('matches.section.incoming')} <span className="count">{groups.incoming.length}</span>
          </h2>
          <p className="muted small">{t('matches.section.incoming.hint')}</p>
          {groups.incoming.map((match) => (
            <MatchCard key={match.id} match={match} now={now}>
              <p className="muted">🔒 {t('worker.privacy')}</p>
              <div className="actions">
                <button type="button" className="button small primary" onClick={() => accept(match)}>
                  {t('matches.accept')}
                </button>
                <button type="button" className="button small secondary" onClick={() => decline(match)}>
                  {t('matches.decline')}
                </button>
              </div>
            </MatchCard>
          ))}
        </>
      )}

      {groups.mutual.length > 0 && (
        <>
          <h2 className="section-title">{t('matches.section.mutual')}</h2>
          <p className="muted small">{t('matches.section.mutual.hint')}</p>
          {groups.mutual.map((match) => (
            <MatchCard key={match.id} match={match} now={now}>
              {match.other_party.phone && <p className="phone">📞 {match.other_party.phone}</p>}
              {match.unread_count > 0 && (
                <p className="unread-text">{t('matches.unread', { count: String(match.unread_count) })}</p>
              )}
              <div className="actions">
                <Link to={`/relations/${match.id}`} className="button small primary">
                  💬 {t('matches.write')}
                </Link>
                {match.other_party.phone && (
                  <a href={`tel:${match.other_party.phone}`} className="button small secondary">
                    {t('matches.call')}
                  </a>
                )}
              </div>
            </MatchCard>
          ))}
        </>
      )}

      {groups.outgoing.length > 0 && (
        <>
          <h2 className="section-title">{t('matches.section.outgoing')}</h2>
          <p className="muted small">{t('matches.section.outgoing.hint')}</p>
          {groups.outgoing.map((match) => (
            <MatchCard key={match.id} match={match} now={now} />
          ))}
        </>
      )}

      {groups.declined.length > 0 && (
        <details className="card declined">
          <summary>
            {t('matches.section.declined')} ({groups.declined.length})
          </summary>
          {groups.declined.map((match) => (
            <div key={match.id} className="declined-row">
              <PartyName match={match} />
              <button type="button" className="button small secondary" onClick={() => accept(match)}>
                {t('matches.reconsider')}
              </button>
            </div>
          ))}
        </details>
      )}
    </section>
  )
}
