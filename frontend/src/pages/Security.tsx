import { useState } from 'react'
import type { FormEvent } from 'react'
import { CheckCircle2 } from 'lucide-react'
import {
  changeEmail,
  changePassword,
  logoutEverywhere,
  requestCode,
  resendEmailLink,
  verifyCode,
} from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import PageHead from '../components/PageHead'
import PasswordField from '../components/PasswordField'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'

type Feedback = { ok: boolean; text: string } | null

function FeedbackLine({ feedback }: { feedback: Feedback }) {
  if (!feedback) return null
  return (
    <p className={feedback.ok ? 'info-banner' : 'error'} role="status">
      {feedback.ok ? '✔ ' : ''}
      {feedback.text}
    </p>
  )
}

/** Confirmer son numéro par code SMS (comptes créés avec un e-mail ou Google / Apple). */
function PhoneCard() {
  const { t, lang } = useI18n()
  const { user, startSession } = useAuth()
  const [sent, setSent] = useState(false)
  const [code, setCode] = useState('')
  const [feedback, setFeedback] = useState<Feedback>(null)

  async function send() {
    setFeedback(null)
    try {
      await requestCode(user!.phone)
      setSent(true)
    } catch (err) {
      setFeedback({ ok: false, text: errorText(err, lang, t, 'login.error') })
    }
  }

  async function confirm(event: FormEvent) {
    event.preventDefault()
    try {
      const response = await verifyCode(user!.phone, code)
      await startSession(response.tokens)
      setFeedback({ ok: true, text: t('security.phone.done') })
      setSent(false)
    } catch (err) {
      setFeedback({ ok: false, text: errorText(err, lang, t, 'verify.error') })
    }
  }

  return (
    <div className="card">
      <h2>{t('security.phone')}</h2>
      <p>
        <strong>{user!.phone}</strong>{' '}
        {user!.phone_verified ? (
          <span className="verified">✔ {t('security.phone.verified')}</span>
        ) : (
          <span className="badge">{t('security.phone.notVerified')}</span>
        )}
      </p>
      {!user!.phone_verified && !sent && (
        <>
          <p className="muted small-text">{t('security.phone.why')}</p>
          <button type="button" className="button small secondary" onClick={send}>
            {t('security.phone.send')}
          </button>
        </>
      )}
      {sent && (
        <form className="stack" onSubmit={confirm}>
          {import.meta.env.DEV && <p className="dev-hint">{t('verify.devHint')}</p>}
          <Field label={t('verify.label')}>
            <input
              className="code-input"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              required
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
            />
          </Field>
          <button type="submit" className="button small primary" disabled={code.length !== 6}>
            {t('verify.submit')}
          </button>
        </form>
      )}
      <FeedbackLine feedback={feedback} />
    </div>
  )
}

function EmailCard() {
  const { t, lang } = useI18n()
  const { user, reload } = useAuth()
  const [email, setEmail] = useState(user!.pending_email || user!.email || '')
  const [current, setCurrent] = useState('')
  const [feedback, setFeedback] = useState<Feedback>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setFeedback(null)
    try {
      await changeEmail(email, current || undefined)
      await reload()
      setCurrent('')
      setFeedback({ ok: true, text: t('security.email.saved') })
    } catch (err) {
      setFeedback({ ok: false, text: errorText(err, lang, t, 'security.error') })
    }
  }

  async function resend() {
    setFeedback(null)
    try {
      await resendEmailLink()
      setFeedback({ ok: true, text: t('security.email.resent') })
    } catch (err) {
      setFeedback({ ok: false, text: errorText(err, lang, t, 'security.error') })
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>{t('email.label')}</h2>
      {user!.email && (
        <p>
          <strong>{user!.email}</strong>{' '}
          {user!.email_verified ? (
            <span className="verified">✔ {t('security.email.verified')}</span>
          ) : (
            <span className="badge">{t('security.email.notVerified')}</span>
          )}
        </p>
      )}
      {user!.pending_email && (
        <>
          <p>
            <strong>{user!.pending_email}</strong> <span className="badge">{t('security.email.notVerified')}</span>
          </p>
          <p className="muted small-text">{t('security.email.why')}</p>
          <button type="button" className="button small secondary" onClick={resend}>
            {t('security.email.resend')}
          </button>
        </>
      )}
      <Field label={t('security.email.label')} hint={t('security.email.hint')}>
        <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </Field>
      {user!.has_password && (
        <PasswordField label={t('password.current')} value={current} onChange={setCurrent} />
      )}
      <FeedbackLine feedback={feedback} />
      <button type="submit" className="button small primary">
        {t('common.save')}
      </button>
    </form>
  )
}

function PasswordCard() {
  const { t, lang } = useI18n()
  const { user, startSession } = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [feedback, setFeedback] = useState<Feedback>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setFeedback(null)
    try {
      const response = await changePassword(next, current || undefined)
      await startSession(response.tokens) // les anciens jetons ne sont plus valables
      setCurrent('')
      setNext('')
      setFeedback({ ok: true, text: t('security.password.saved') })
    } catch (err) {
      setFeedback({ ok: false, text: errorText(err, lang, t, 'security.error') })
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>{t('password.label')}</h2>
      {!user!.has_password && <p className="muted small-text">{t('security.password.none')}</p>}
      {user!.has_password && <PasswordField label={t('password.current')} value={current} onChange={setCurrent} />}
      <PasswordField
        label={t('password.new')}
        hint={t('password.rules')}
        autoComplete="new-password"
        value={next}
        onChange={setNext}
      />
      <FeedbackLine feedback={feedback} />
      <button type="submit" className="button small primary">
        {user!.has_password ? t('security.password.change') : t('security.password.create')}
      </button>
    </form>
  )
}

/** « Se déconnecter de tous les appareils » (téléphone perdu, session suspecte). */
function SessionsCard() {
  const { t } = useI18n()
  const { logout } = useAuth()
  const [error, setError] = useState(false)

  async function everywhere() {
    if (!window.confirm(t('security.sessions.confirm'))) return
    try {
      await logoutEverywhere()
      logout()
    } catch {
      setError(true)
    }
  }

  return (
    <div className="card">
      <h2>{t('security.sessions')}</h2>
      <p className="muted small-text">{t('security.sessions.hint')}</p>
      {error && <p className="error">{t('security.error')}</p>}
      <button type="button" className="button small danger-outline" onClick={everywhere}>
        {t('security.sessions.button')}
      </button>
    </div>
  )
}

const TIPS: TranslationKey[] = ['security.tip1', 'security.tip2', 'security.tip3', 'security.tip4', 'security.tip5']

/** Écran « Sécurité & confidentialité ». */
export default function Security() {
  const { t } = useI18n()
  const { user } = useAuth()
  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={t('security.title')} />

      <div className="card">
        <h2>{t('security.tips')}</h2>
        <ul className="tips">
          {TIPS.map((tip) => (
            <li key={tip}>
              <CheckCircle2 size={18} aria-hidden="true" /> {t(tip)}
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2>{t('security.privacy')}</h2>
        <p>{t('security.privacy.before')}</p>
        <p>{t('security.privacy.after')}</p>
        <p className="muted small-text">{t('security.privacy.team')}</p>
      </div>

      <h2 className="overline">{t('security.account')}</h2>
      <PhoneCard />
      <EmailCard />
      <PasswordCard />
      <SessionsCard />
      {user!.social_providers.length > 0 && (
        <div className="card">
          <h2>{t('security.linked')}</h2>
          <p>{user!.social_providers.map((p) => (p === 'google' ? 'Google' : 'Apple')).join(', ')}</p>
        </div>
      )}
    </section>
  )
}
