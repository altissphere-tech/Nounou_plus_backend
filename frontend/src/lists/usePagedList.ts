import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { fetchPage } from '../api/search'
import type { Page } from '../api/types'

interface PagedList<T> {
  items: T[]
  count: number
  loading: boolean
  failed: boolean
  /** Le serveur refuse l'accès (403), par ex. travailleur pas encore vérifié. */
  forbidden: boolean
  hasMore: boolean
  loadMore: () => void
}

interface State<T> {
  key: string | null // filtres correspondant aux résultats affichés
  items: T[]
  count: number
  next: string | null
  failed: boolean
  forbidden: boolean
  loadingMore: boolean
}

/**
 * Liste paginée de l'API : charge la première page via `load`, puis les pages
 * suivantes avec « Voir plus ». Se recharge quand `key` change (ex : filtres) ;
 * pendant ce rechargement, les anciens résultats ne sont plus affichés.
 */
export function usePagedList<T>(load: () => Promise<Page<T>>, key: string): PagedList<T> {
  const [state, setState] = useState<State<T>>({
    key: null,
    items: [],
    count: 0,
    next: null,
    failed: false,
    forbidden: false,
    loadingMore: false,
  })

  useEffect(() => {
    let cancelled = false
    load().then(
      (page) =>
        !cancelled &&
        setState({
          key,
          items: page.results,
          count: page.count,
          next: page.next,
          failed: false,
          forbidden: false,
          loadingMore: false,
        }),
      (error) =>
        !cancelled &&
        setState({
          key,
          items: [],
          count: 0,
          next: null,
          failed: true,
          forbidden: error instanceof ApiError && error.status === 403,
          loadingMore: false,
        }),
    )
    return () => {
      cancelled = true
    }
    // `load` change à chaque affichage : on recharge seulement quand `key` change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  const loadMore = useCallback(() => {
    if (!state.next) return
    setState((s) => ({ ...s, loadingMore: true }))
    fetchPage<T>(state.next).then(
      (page) =>
        setState((s) => ({ ...s, items: [...s.items, ...page.results], next: page.next, loadingMore: false })),
      () => setState((s) => ({ ...s, failed: true, loadingMore: false })),
    )
  }, [state.next])

  const current = state.key === key // résultats à jour pour les filtres demandés ?
  return {
    items: current ? state.items : [],
    count: current ? state.count : 0,
    loading: !current || state.loadingMore,
    failed: current && state.failed,
    forbidden: current && state.forbidden,
    hasMore: current && Boolean(state.next),
    loadMore,
  }
}
