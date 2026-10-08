/**
 * Chrome (Android) annonce qu'on peut installer l'application avec l'événement
 * « beforeinstallprompt », souvent dès l'ouverture. Il est capté ici, au démarrage,
 * pour que la carte « Installer » le retrouve même si son écran s'affiche plus tard.
 */
export interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let deferred: BeforeInstallPromptEvent | null = null
const listeners = new Set<() => void>()

function publish(event: BeforeInstallPromptEvent | null) {
  deferred = event
  listeners.forEach((listener) => listener())
}

export function captureInstallEvent(): void {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault() // on affiche notre propre bouton
    publish(event as BeforeInstallPromptEvent)
  })
  window.addEventListener('appinstalled', () => publish(null))
}

export function currentInstallEvent(): BeforeInstallPromptEvent | null {
  return deferred
}

/** Prévient quand l'installation devient possible (ou n'est plus proposée). */
export function onInstallEvent(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

/** Après usage, l'événement ne peut plus servir. */
export function clearInstallEvent(): void {
  publish(null)
}
