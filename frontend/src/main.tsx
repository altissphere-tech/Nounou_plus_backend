import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { initialLanguage, loadLanguage } from './i18n/languages'
import { registerServiceWorker } from './pwa/register'
import { preloadScreensWhenIdle } from './routing/lazyScreen'
import '@fontsource-variable/nunito'
import './styles.css'

/** Active le style (chargé sans bloquer l'écran de démarrage) et attend qu'il soit arrivé. */
function stylesReady(): Promise<void> {
  const link = document.querySelector<HTMLLinkElement>('link[data-app-css]')
  if (!link) return Promise.resolve() // en développement, le style est déjà là
  link.media = 'all'
  if (link.sheet) return Promise.resolve()
  return new Promise((resolve) => {
    link.addEventListener('load', () => resolve(), { once: true })
    link.addEventListener('error', () => resolve(), { once: true })
  })
}

// La langue de la personne et le style sont prêts avant le premier affichage
Promise.all([loadLanguage(initialLanguage()).catch(() => undefined), stylesReady()]).finally(() =>
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  ),
)

registerServiceWorker()
preloadScreensWhenIdle()
