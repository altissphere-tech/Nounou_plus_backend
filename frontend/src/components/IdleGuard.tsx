import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { IDLE_LIMIT_MS, idleState, lastActivity, markActivity, rememberIdleLogout } from '../auth/idle'
import { useI18n } from '../i18n/I18nContext'

const ACTIVITY_EVENTS = ['pointerdown', 'keydown', 'scroll', 'touchstart'] as const
const CHECK_EVERY_MS = 5000

/**
 * Surveille l'inactivité de la personne connectée : fenêtre d'avertissement
 * 1 minute avant, puis déconnexion au bout de 30 minutes sans geste.
 */
export default function IdleGuard() {
  const { user, logout } = useAuth()
  const { t } = useI18n()
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null)
  // Copie lisible par les écouteurs d'événements sans les re-créer
  const secondsLeftRef = useRef<number | null>(null)

  useEffect(() => {
    if (!user) return
    markActivity()
    let lastWrite = 0
    const onActivity = () => {
      // Pendant l'avertissement, seul le bouton « Rester connecté(e) » prolonge la session
      if (secondsLeftRef.current !== null) return
      const now = Date.now()
      if (now - lastWrite > 1000) {
        markActivity(now)
        lastWrite = now
      }
    }
    const check = () => {
      const now = Date.now()
      const last = lastActivity() ?? now
      const state = idleState(last, now)
      if (state === 'expired') {
        rememberIdleLogout()
        secondsLeftRef.current = null
        setSecondsLeft(null)
        logout()
      } else if (state === 'warning') {
        const left = Math.max(0, Math.ceil((last + IDLE_LIMIT_MS - now) / 1000))
        secondsLeftRef.current = left
        setSecondsLeft(left)
      } else {
        secondsLeftRef.current = null
        setSecondsLeft(null)
      }
    }
    ACTIVITY_EVENTS.forEach((name) => window.addEventListener(name, onActivity, { passive: true }))
    // En revenant sur l'application (téléphone déverrouillé), vérification immédiate
    document.addEventListener('visibilitychange', check)
    const timer = window.setInterval(check, CHECK_EVERY_MS)
    return () => {
      ACTIVITY_EVENTS.forEach((name) => window.removeEventListener(name, onActivity))
      document.removeEventListener('visibilitychange', check)
      window.clearInterval(timer)
    }
  }, [user, logout])

  if (!user || secondsLeft === null) return null

  function stay() {
    markActivity()
    secondsLeftRef.current = null
    setSecondsLeft(null)
  }

  return (
    <div className="modal-backdrop">
      <div className="card modal" role="alertdialog" aria-modal="true" aria-labelledby="idle-title">
        <h2 id="idle-title">{t('idle.title')}</h2>
        <p>{t('idle.text', { seconds: String(secondsLeft) })}</p>
        <button type="button" className="button primary" onClick={stay} autoFocus>
          {t('idle.stay')}
        </button>
        <button type="button" className="button secondary" onClick={logout}>
          {t('home.logout')}
        </button>
      </div>
    </div>
  )
}
