import { api } from './client'
import type { InterestResponse, Match, Message, Page } from './types'

// Endpoints « Mise en relation » et « Messagerie ».

/** Toutes les mises en relation (pages de 100, largement suffisant en V1). */
export const listMatches = () => api<Page<Match>>('GET', '/api/matches/?page_size=100')

/** Accepter un intérêt reçu (ou revenir sur un refus) : on se déclare intéressé par l'autre profil. */
export const acceptMatch = (match: Match) =>
  api<InterestResponse>('POST', '/api/matches/interest/', { profile_id: match.other_party.id })

export const declineMatch = (id: number) => api<{ match: Match }>('POST', `/api/matches/${id}/decline/`)

export const getMessages = (matchId: number) =>
  api<{ count: number; results: Message[] }>('GET', `/api/matches/${matchId}/messages/`)

export const sendMessage = (matchId: number, content: string) =>
  api<Message>('POST', `/api/matches/${matchId}/messages/`, { content })
