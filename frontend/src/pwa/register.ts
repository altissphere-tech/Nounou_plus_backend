/**
 * Active le service worker (installation sur l'écran d'accueil + ouverture hors
 * connexion). Seulement dans la version finale : en développement, il gênerait
 * le rechargement automatique des modifications.
 */
export function registerServiceWorker(): void {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Sans service worker, l'application fonctionne normalement (en ligne)
    })
  })
}
