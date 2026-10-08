import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { phoneVerificationRequired, socialLogin } from '../api/accounts'
import { ApiError } from '../api/client'
import type { SocialProvider } from '../api/types'
import { errorText } from '../components/errors'
import { useI18n } from '../i18n/I18nContext'
import { useAuth } from './AuthContext'

/**
 * Après Google / Apple : connexion directe si le compte existe, sinon écran
 * « Dernière étape » (choix du profil + numéro de téléphone).
 */
export function useSocialLogin() {
  const { startSession } = useAuth()
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  async function handleToken(provider: SocialProvider, idToken: string) {
    setError('')
    try {
      const response = await socialLogin(provider, idToken)
      await startSession(response.tokens)
      navigate('/accueil', { replace: true })
    } catch (err) {
      const data = err instanceof ApiError ? (err.data as { registration_required?: boolean; email?: string }) : null
      const verification = phoneVerificationRequired(data)
      if (verification) {
        navigate('/code', { state: { phone: verification.phone } })
      } else if (data?.registration_required) {
        navigate('/inscription/finaliser', { state: { provider, idToken, email: data.email ?? null } })
      } else {
        setError(errorText(err, lang, t, 'social.error'))
      }
    }
  }

  return { handleToken, error, setError }
}
