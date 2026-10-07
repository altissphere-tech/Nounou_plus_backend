import { useEffect, useRef, useState } from 'react'
import type { AuthOptions, SocialProvider } from '../api/types'
import { authOptions, renderGoogleButton, signInWithApple } from '../auth/social'
import { useI18n } from '../i18n/I18nContext'

function GoogleLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
      <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
    </svg>
  )
}

function AppleLogo() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
      <path d="M16.37 12.6c-.02-2.1 1.72-3.1 1.8-3.15-.98-1.43-2.5-1.63-3.04-1.65-1.29-.13-2.52.76-3.18.76-.65 0-1.66-.74-2.73-.72-1.4.02-2.7.82-3.42 2.08-1.46 2.53-.37 6.27 1.05 8.32.7 1 1.52 2.13 2.6 2.09 1.05-.04 1.44-.67 2.7-.67 1.26 0 1.62.67 2.72.65 1.13-.02 1.84-1.02 2.52-2.03.8-1.16 1.13-2.29 1.14-2.35-.02-.01-2.19-.84-2.16-3.33zM14.3 6.43c.57-.7.96-1.66.85-2.63-.83.03-1.83.55-2.42 1.24-.53.61-1 1.6-.87 2.54.92.07 1.87-.47 2.44-1.15z" />
    </svg>
  )
}

/**
 * Boutons « Google » et « Apple ». Tant que l'équipe n'a pas créé les comptes
 * développeur (identifiants dans le fichier .env du serveur), ils restent grisés.
 */
export default function SocialButtons({
  onToken,
  onError,
}: {
  onToken: (provider: SocialProvider, idToken: string) => void
  onError: (message: string) => void
}) {
  const { t, lang } = useI18n()
  const [options, setOptions] = useState<AuthOptions | null>(null)
  const googleBox = useRef<HTMLDivElement>(null)
  const [googleReady, setGoogleReady] = useState(false)
  // Les fonctions de l'écran parent sont gardées à part : le bouton Google n'est dessiné qu'une fois
  const callbacks = useRef({ onToken, onError })
  useEffect(() => {
    callbacks.current = { onToken, onError }
  })

  useEffect(() => {
    authOptions().then(setOptions, () => setOptions(null))
  }, [])

  useEffect(() => {
    if (!options?.google_client_id || !googleBox.current) return
    renderGoogleButton(googleBox.current, options.google_client_id, lang, (token) =>
      callbacks.current.onToken('google', token),
    ).then(
      () => setGoogleReady(true),
      () => callbacks.current.onError(t('social.unavailable')),
    )
  }, [options, lang, t])

  async function apple() {
    try {
      onToken('apple', await signInWithApple(options!.apple_client_id))
    } catch {
      onError(t('social.error'))
    }
  }

  const googleOn = Boolean(options?.google_client_id)
  const appleOn = Boolean(options?.apple_client_id)

  return (
    <div className="social">
      <div className="social-buttons">
        {googleOn ? (
          <div ref={googleBox} className="google-box" aria-busy={!googleReady} />
        ) : (
          <button type="button" className="social-button" disabled>
            <GoogleLogo /> Google
          </button>
        )}
        <button type="button" className="social-button" disabled={!appleOn} onClick={apple}>
          <AppleLogo /> Apple
        </button>
      </div>
      {(!googleOn || !appleOn) && <p className="social-soon">{t('social.soon')}</p>}
      <p className="divider">
        <span>{t('common.or')}</span>
      </p>
    </div>
  )
}
