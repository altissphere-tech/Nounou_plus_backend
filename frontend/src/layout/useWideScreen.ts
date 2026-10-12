import { useSyncExternalStore } from 'react'

/** Largeur à partir de laquelle une colonne d'informations s'ajoute à droite (ordinateur). */
export const WIDE_QUERY = '(min-width: 1280px)'

function subscribe(onChange: () => void) {
  const query = window.matchMedia?.(WIDE_QUERY)
  query?.addEventListener('change', onChange)
  return () => query?.removeEventListener('change', onChange)
}

const isWide = () => window.matchMedia?.(WIDE_QUERY).matches ?? false

/**
 * True sur un grand écran. La colonne de droite n'est créée (et ses données
 * chargées) que dans ce cas : rien ne change sur téléphone ni sur tablette.
 */
export function useWideScreen(): boolean {
  return useSyncExternalStore(subscribe, isWide, () => false)
}
