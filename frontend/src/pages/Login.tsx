import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginWithEmail, phoneVerificationRequired, requestCode } from '../api/accounts'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useSocialLogin } from '../auth/useSocialLogin'
import AuthTabs from '../components/AuthTabs'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import MethodSwitch from '../components/MethodSwitch'
import type { Method } from '../components/MethodSwitch'
import PasswordField from '../components/PasswordField'
import PhoneField from '../components/PhoneField'
import SocialButtons from '../components/SocialButtons'
import { useI18n } from '../i18n/I18nContext'

export default function Login() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const social = useSocialLogin()
  const [method, setMethod] = useState<Method>('phone')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (method === 'phone') {
        await requestCode(phone)
        navigate('/code', { state: { phone } })
      } else {
        const response = await loginWithEmail(email, password)
        await startSession(response.tokens)
        navigate('/accueil', { replace: true })
      }
    } catch (err) {
      // Numéro jamais confirmé : un code vient d'être envoyé, on le demande
      const verification = err instanceof ApiError ? phoneVerificationRequired(err.data) : null
      if (verification) {
        navigate('/code', { state: { phone: verification.phone } })
        return
      }
      setError(errorText(err, lang, t, method === 'phone' ? 'login.error' : 'login.emailError'))
    } finally {
      setBusy(false)
    }
  }

  const shownError = error || social.error

  return (
    <form className="card auth-card" onSubmit={submit}>
      <div>
        <h1>{t('login.title')}</h1>
        <p className="muted">{t('login.subtitle')}</p>
      </div>
      <AuthTabs />
      <SocialButtons onToken={social.handleToken} onError={social.setError} />
      <MethodSwitch
        value={method}
        onChange={(next) => {
          setMethod(next)
          setError('')
        }}
      />
      {method === 'phone' ? (
        <PhoneField value={phone} onChange={setPhone} />
      ) : (
        <>
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
          <PasswordField label={t('password.label')} value={password} onChange={setPassword} />
          <Link to="/mot-de-passe-oublie" className="link forgot">
            {t('login.forgot')}
          </Link>
        </>
      )}
      {shownError && <p className="error" role="alert">{shownError}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : method === 'phone' ? t('login.submit') : t('login.submitEmail')}
      </button>
      <Link to="/inscription" className="link">
        {t('login.noAccount')}
      </Link>
    </form>
  )
}
