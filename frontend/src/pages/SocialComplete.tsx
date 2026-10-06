import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { socialLogin } from '../api/accounts'
import type { SocialProvider } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { errorText } from '../components/errors'
import PhoneField from '../components/PhoneField'
import RoleCards from '../components/RoleCards'
import type { Role } from '../components/RoleCards'
import TermsNote from '../components/TermsNote'
import { useI18n } from '../i18n/I18nContext'

interface SocialState {
  provider: SocialProvider
  idToken: string
  email: string | null
}

/** Première connexion avec Google / Apple : choix du profil et numéro de téléphone. */
export default function SocialComplete() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const state = useLocation().state as SocialState | null
  const [role, setRole] = useState<Role>('client')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!state?.idToken) return <Navigate to="/inscription" replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const response = await socialLogin(state!.provider, state!.idToken, { role, phone })
      await startSession(response.tokens)
      navigate('/accueil', { replace: true })
    } catch (err) {
      setError(errorText(err, lang, t, 'social.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card auth-card" onSubmit={submit}>
      <h1>{t('social.complete.title')}</h1>
      <p className="muted">
        {state.email ? t('social.complete.intro', { email: state.email }) : t('social.complete.introNoEmail')}
      </p>
      <RoleCards value={role} onChange={setRole} />
      <PhoneField value={phone} onChange={setPhone} />
      <p className="field-hint">{t('register.phoneWhy')}</p>
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : t('social.complete.submit')}
      </button>
      <TermsNote />
    </form>
  )
}
