import { useEffect, useSyncExternalStore } from 'react'
import { listFavorites, setFavorite } from '../api/favorites'

/**
 * Favoris de la personne connectée, gardés en mémoire pour afficher les cœurs
 * des cartes sans redemander la liste à chaque écran.
 */
type Kind = 'workers' | 'jobs'

let state: { owner: number | null; workers: Set<number>; jobs: Set<number> } = {
  owner: null,
  workers: new Set(),
  jobs: new Set(),
}
let loading: number | null = null
const listeners = new Set<() => void>()

function emit(next: typeof state) {
  state = next
  listeners.forEach((listener) => listener())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function load(owner: number) {
  if (state.owner === owner || loading === owner) return
  loading = owner
  listFavorites().then(
    (favorites) =>
      emit({
        owner,
        workers: new Set(favorites.workers.map((w) => w.id)),
        jobs: new Set(favorites.jobs.map((j) => j.id)),
      }),
    () => {},
  ).finally(() => {
    loading = null
  })
}

/** Identifiants mis en favori pour l'utilisateur `owner` (null tant que la liste n'est pas chargée). */
export function useFavoriteIds(kind: Kind, owner: number | undefined): Set<number> | null {
  useEffect(() => {
    if (owner !== undefined) load(owner)
  }, [owner])
  const snapshot = useSyncExternalStore(subscribe, () => state)
  return snapshot.owner === owner ? snapshot[kind] : null
}

/** Ajoute ou retire un favori (l'affichage change tout de suite, et revient en arrière en cas d'échec). */
export async function toggleFavorite(kind: Kind, id: number): Promise<void> {
  const on = !state[kind].has(id)
  const apply = (value: boolean) => {
    const ids = new Set(state[kind])
    if (value) ids.add(id)
    else ids.delete(id)
    emit({ ...state, [kind]: ids })
  }
  apply(on)
  try {
    await setFavorite(kind, id, on)
  } catch (error) {
    apply(!on)
    throw error
  }
}
