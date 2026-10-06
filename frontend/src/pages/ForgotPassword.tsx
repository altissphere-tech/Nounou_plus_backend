import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/accounts'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import { useI18n } from '../i18n/I18nContext'

export default function ForgotPassword() {
  const { t, lang } = useI18n()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      await forgotPassword(email)
      setSent(true)
    } catch (err) {
      setError(errorText(err, lang, t, 'forgot.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card auth-card" onSubmit={submit}>
      <h1>{t('forgot.title')}</h1>
      {sent ? (
        <>
          <p className="info-banner" role="status">✔ {t('forgot.sent')}</p>
          {import.meta.env.DEV && <p className="dev-hint">{t('forgot.devHint')}</p>}
        </>
      ) : (
        <>
          <p className="muted">{t('forgot.intro')}</p>
          <Field label={t('email.label')}>
            <input
              type="email"
              autoComplete="email"
              inputMode="email"
              required
              placeholder={t('email.placeholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          {error && <p className="error" role="alert">{error}</p>}
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? t('common.loading') : t('forgot.submit')}
          </button>
          <p className="field-hint">{t('forgot.noEmail')}</p>
        </>
      )}
      <Link to="/connexion" className="link">
        {t('forgot.back')}
      </Link>
    </form>
  )
}
