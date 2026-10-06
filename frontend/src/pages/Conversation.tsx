import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { ApiError } from '../api/client'
import { getMessages, listMatches, sendMessage } from '../api/matches'
import type { Match, Message } from '../api/types'
import Avatar from '../components/Avatar'
import { useI18n } from '../i18n/I18nContext'
import { refreshNews } from '../matches/groups'

const REFRESH_EVERY_MS = 8000 // nouveaux messages récupérés toutes les 8 secondes

/** Conversation avec l'autre personne d'un match mutuel. */
export default function Conversation() {
  const { t, lang } = useI18n()
  const matchId = Number(useParams().id)
  const [match, setMatch] = useState<Match | null>(null)
  const [messages, setMessages] = useState<Message[] | undefined>(undefined)
  const [closed, setClosed] = useState(false)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)

  const refresh = useCallback(() => {
    getMessages(matchId).then(
      (data) => {
        setMessages(data.results)
        refreshNews()
      },
      (err) => {
        if (err instanceof ApiError && (err.status === 403 || err.status === 404)) setClosed(true)
      },
    )
  }, [matchId])

  useEffect(() => {
    listMatches().then((page) => setMatch(page.results.find((m) => m.id === matchId) ?? null))
    refresh()
    const timer = window.setInterval(refresh, REFRESH_EVERY_MS)
    return () => window.clearInterval(timer)
  }, [matchId, refresh])

  // Fait défiler jusqu'au dernier message
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' })
  }, [messages?.length])

  async function send(event: FormEvent) {
    event.preventDefault()
    const content = draft.trim()
    if (!content) return
    setSending(true)
    setError('')
    try {
      const message = await sendMessage(matchId, content)
      setMessages((current) => [...(current ?? []), message])
      setDraft('')
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) setClosed(true)
      else setError(t('chat.error'))
    } finally {
      setSending(false)
    }
  }

  const time = (iso: string) =>
    new Date(iso).toLocaleString(lang === 'fr' ? 'fr-FR' : 'en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })

  return (
    <section className="chat">
      <div className="page-head chat-head">
        <div className="page-head-row">
          <Link to="/relations" className="icon-button" aria-label={t('chat.back')}>
            <ArrowLeft size={20} />
          </Link>
          {match && (
            <>
              <Avatar
                name={`${match.other_party.first_name} ${match.other_party.last_name}`}
                src={match.other_party.photo_url}
                size={42}
              />
              <div className="chat-party">
                <h1 className="profile-name">
                  {match.other_party.first_name} {match.other_party.last_name}
                </h1>
                {match.other_party.phone && (
                  <a href={`tel:${match.other_party.phone}`} className="phone">
                    📞 {match.other_party.phone}
                  </a>
                )}
              </div>
            </>
          )}
        </div>
      </div>
      <div className="chat-top">
        <p className="chat-safety">🛡️ {t('chat.safety')}</p>
      </div>

      {closed ? (
        <p className="card muted">{t('chat.closed')}</p>
      ) : messages === undefined ? (
        <p className="muted">{t('common.loading')}</p>
      ) : (
        <>
          <div className="messages" aria-live="polite">
            {messages.length === 0 && <p className="muted center">{t('chat.empty')}</p>}
            {messages.map((message) => (
              <div key={message.id} className={`bubble ${message.is_mine ? 'mine' : 'theirs'}`}>
                <p className={message.is_hidden ? 'muted' : 'pre-line'}>
                  {message.is_hidden ? t('chat.hidden') : message.content}
                </p>
                <span className="bubble-time">{time(message.created_at)}</span>
              </div>
            ))}
            <div ref={bottom} />
          </div>
          {error && <p className="error" role="alert">{error}</p>}
          <form className="chat-form" onSubmit={send}>
            <textarea
              rows={1}
              maxLength={2000}
              aria-label={t('chat.placeholder')}
              placeholder={t('chat.placeholder')}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button type="submit" className="button primary" disabled={sending || !draft.trim()}>
              {t('chat.send')}
            </button>
          </form>
        </>
      )}
    </section>
  )
}
