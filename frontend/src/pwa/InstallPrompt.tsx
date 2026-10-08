import { useState, useSyncExternalStore } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { clearInstallEvent, currentInstallEvent, onInstallEvent } from './installEvent'

const DISMISSED_KEY = 'nounou.install.dismissed'

function isStandalone(): boolean {
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function isIos(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

function wasDismissed(): boolean {
  try {
    return localStorage.getItem(DISMISSED_KEY) === '1'
  } catch {
    return false
  }
}

/**
 * Carte « Installer l'application » :
 * - Android (Chrome) : bouton qui ouvre la fenêtre d'installation ;
 * - iPhone (Safari) : explication « Partager → Sur l'écran d'accueil ».
 * Masquée si l'application est déjà installée ou si l'utilisateur l'a fermée.
 */
export default function InstallPrompt() {
  const { t } = useI18n()
  // Événement capté au démarrage (pwa/installEvent.ts), même avant l'affichage de cet écran
  const deferred = useSyncExternalStore(onInstallEvent, currentInstallEvent)
  const [hidden, setHidden] = useState(() => isStandalone() || wasDismissed())

  function dismiss() {
    setHidden(true)
    try {
      localStorage.setItem(DISMISSED_KEY, '1')
    } catch {
      // Sans stockage, la carte réapparaîtra à la prochaine visite
    }
  }

  async function install() {
    if (!deferred) return
    await deferred.prompt()
    const choice = await deferred.userChoice
    if (choice.outcome === 'accepted') setHidden(true)
    clearInstallEvent()
  }

  if (hidden || (!deferred && !isIos())) return null

  return (
    <div className="card install">
      <img src="/logo.webp" alt="" width={44} height={44} className="logo-icon" />
      <div className="install-text">
        <strong>{t('install.title')}</strong>
        <span>{deferred ? t('install.text') : t('install.ios')}</span>
      </div>
      <div className="install-actions">
        {deferred && (
          <button type="button" className="button small primary" onClick={install}>
            {t('install.button')}
          </button>
        )}
        <button type="button" className="link" onClick={dismiss} aria-label={t('install.later')}>
          {t('install.later')}
        </button>
      </div>
    </div>
  )
}
