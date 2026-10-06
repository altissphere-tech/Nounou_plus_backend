import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register, registerWithEmail } from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import { useSocialLogin } from '../auth/useSocialLogin'
import AuthTabs from '../components/AuthTabs'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import MethodSwitch from '../components/MethodSwitch'
import type { Method } from '../components/MethodSwitch'
import PasswordField from '../components/PasswordField'
import PhoneField from '../components/PhoneField'
import RoleCards from '../components/RoleCards'
import type { Role } from '../components/RoleCards'
import SocialButtons from '../components/SocialButtons'
import TermsNote from '../components/TermsNote'
import { useI18n } from '../i18n/I18nContext'

export default function Register() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const social = useSocialLogin()
  const [role, setRole] = useState<Role>('client')
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
        await register(phone, role)
        navigate('/code', { state: { phone } })
      } else {
        const response = await registerWithEmail({ phone, role, email, password })
        await startSession(response.tokens)
        navigate('/accueil', { replace: true })
      }
    } catch (err) {
      setError(errorText(err, lang, t, 'register.error'))
    } finally {
      setBusy(false)
    }
  }

  const shownError = error || social.error

  return (
    <form className="card auth-card" onSubmit={submit}>
      <h1>{t('register.title')}</h1>
      <AuthTabs />
      <RoleCards value={role} onChange={setRole} />
      <SocialButtons onToken={social.handleToken} onError={social.setError} />
      <MethodSwitch
        value={method}
        onChange={(next) => {
          setMethod(next)
          setError('')
        }}
      />
      {method === 'email' && (
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
          <PasswordField
            label={t('password.label')}
            hint={t('password.rules')}
            autoComplete="new-password"
            value={password}
            onChange={setPassword}
          />
        </>
      )}
      <PhoneField value={phone} onChange={setPhone} />
      {method === 'email' && <p className="field-hint">{t('register.phoneWhy')}</p>}
      {shownError && <p className="error" role="alert">{shownError}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : method === 'phone' ? t('register.submit') : t('register.submitEmail')}
      </button>
      <TermsNote />
      <Link to="/connexion" className="link">
        {t('register.haveAccount')}
      </Link>
    </form>
  )
}
