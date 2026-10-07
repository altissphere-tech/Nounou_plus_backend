import { api } from './client'
import type { Favorites } from './types'

export const listFavorites = () => api<Favorites>('GET', '/api/favorites/')

export const setFavorite = (kind: 'workers' | 'jobs', id: number, on: boolean) =>
  api<{ message: string }>(on ? 'PUT' : 'DELETE', `/api/favorites/${kind}/${id}/`)
