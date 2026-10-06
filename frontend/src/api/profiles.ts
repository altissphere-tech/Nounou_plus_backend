import { ApiError, api } from './client'
import type { ClientProfile, ClientProfileInput, WorkerProfile, WorkerProfileInput } from './types'

// Endpoints « Travailleurs » et « Clients » : le profil de l'utilisateur connecté.

/** Retourne null si le profil n'a pas encore été créé (réponse 404). */
async function orNull<T>(request: Promise<T>): Promise<T | null> {
  try {
    return await request
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export function getMyWorkerProfile() {
  return orNull(api<WorkerProfile>('GET', '/api/workers/profile/me/'))
}

export function getMyClientProfile() {
  return orNull(api<ClientProfile>('GET', '/api/clients/profile/me/'))
}

export function saveWorkerProfile(data: WorkerProfileInput, exists: boolean) {
  return exists
    ? api<{ profile: WorkerProfile }>('PATCH', '/api/workers/profile/me/', data)
    : api<{ profile: WorkerProfile }>('POST', '/api/workers/profile/', data)
}

export function saveClientProfile(data: ClientProfileInput, exists: boolean) {
  return exists
    ? api<{ profile: ClientProfile }>('PATCH', '/api/clients/profile/me/', data)
    : api<{ profile: ClientProfile }>('POST', '/api/clients/profile/', data)
}
