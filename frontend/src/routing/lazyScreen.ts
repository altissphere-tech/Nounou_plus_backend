import { lazy } from 'react'
import type { ComponentType } from 'react'

/**
 * Écran téléchargé seulement quand on l'ouvre : la première ouverture de
 * l'application reste légère (important en 3G). `preload()` permet de le
 * télécharger à l'avance, quand le téléphone n'a rien d'autre à faire.
 */
type Loader = () => Promise<{ default: ComponentType }>

const loaders: Loader[] = []

export function lazyScreen(load: Loader) {
  loaders.push(load)
  return lazy(load)
}

/** Connexion économe en données (option du téléphone) ou très lente : on ne télécharge rien d'avance. */
function saveData(): boolean {
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } })
    .connection
  return Boolean(connection?.saveData) || /(^|-)2g$/.test(connection?.effectiveType ?? '')
}

/**
 * Une fois l'application affichée, télécharge discrètement les autres écrans
 * (l'un après l'autre) : ils s'ouvriront ensuite instantanément, et aussi sans
 * connexion grâce au service worker.
 */
export function preloadScreensWhenIdle(): void {
  if (saveData()) return
  const idle = (callback: () => void) => {
    if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(callback)
    else setTimeout(callback, 2000)
  }
  const next = (index: number) => {
    if (index >= loaders.length || !navigator.onLine) return
    loaders[index]().then(
      () => idle(() => next(index + 1)),
      () => undefined, // réseau coupé : l'écran sera téléchargé à l'ouverture
    )
  }
  window.addEventListener('load', () => idle(() => next(0)), { once: true })
}
