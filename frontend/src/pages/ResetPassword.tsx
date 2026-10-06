import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/accounts'
import { errorText } from '../components/errors'
import PasswordField from '../components/PasswordField'
import { useI18n } from '../i18n/I18nContext'

/** Page ouverte depuis le lien reçu par e-mail : choix du nouveau mot de passe. */
export default function ResetPassword() {
  const { t, lang } = useI18n()
  const [params] = useSearchParams()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (password !== confirm) {
      setError(t('password.mismatch'))
      return
    }
    setBusy(true)
    try {
      await resetPassword(params.get('uid') ?? '', params.get('token') ?? '', password)
      setDone(true)
    } catch (err) {
      setError(errorText(err, lang, t, 'reset.error'))
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="card auth-card">
        <h1>{t('reset.title')}</h1>
        <p className="info-banner" role="status">✔ {t('reset.done')}</p>
        <Link to="/connexion" className="button primary">
          {t('reset.login')}
        </Link>
      </div>
    )
  }

  return (
    <form className="card auth-card" onSubmit={submit}>
      <h1>{t('reset.title')}</h1>
      <PasswordField
        label={t('password.new')}
        hint={t('password.rules')}
        autoComplete="new-password"
        value={password}
        onChange={setPassword}
      />
      <PasswordField label={t('password.confirm')} autoComplete="new-password" value={confirm} onChange={setConfirm} />
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : t('reset.submit')}
      </button>
      <Link to="/mot-de-passe-oublie" className="link">
        {t('reset.newLink')}
      </Link>
    </form>
  )
}
