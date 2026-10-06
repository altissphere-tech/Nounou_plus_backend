import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { requestCode } from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import { errorText } from '../components/errors'
import { useI18n } from '../i18n/I18nContext'

export default function VerifyCode() {
  const { t, lang } = useI18n()
  const { login } = useAuth()
  const navigate = useNavigate()
  const phone = (useLocation().state as { phone?: string } | null)?.phone
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)

  // Arrivée directe sur cette page sans numéro : retour à la connexion
  if (!phone) return <Navigate to="/connexion" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setInfo('')
    setBusy(true)
    try {
      await login(phone!, code)
      navigate('/accueil', { replace: true })
    } catch (err) {
      setError(errorText(err, lang, t, 'verify.error'))
    } finally {
      setBusy(false)
    }
  }

  async function resend() {
    setError('')
    try {
      await requestCode(phone!)
      setInfo(t('verify.resent'))
    } catch (err) {
      setError(errorText(err, lang, t, 'login.error'))
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('verify.title')}</h1>
      <p className="muted">{t('verify.sentTo', { phone })}</p>
      {import.meta.env.DEV && <p className="dev-hint">{t('verify.devHint')}</p>}
      <label className="field">
        <span className="field-label">{t('verify.label')}</span>
        <input
          className="code-input"
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="[0-9]{6}"
          maxLength={6}
          required
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
        />
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      {info && <p className="info">{info}</p>}
      <button type="submit" className="button primary" disabled={busy || code.length !== 6}>
        {busy ? t('common.loading') : t('verify.submit')}
      </button>
      <button type="button" className="link" onClick={resend}>
        {t('verify.resend')}
      </button>
    </form>
  )
}
