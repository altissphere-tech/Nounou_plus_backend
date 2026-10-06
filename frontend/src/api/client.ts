/**
 * Petit client pour l'API NOUNOU+.
 *
 * - Ajoute automatiquement le token de connexion (JWT) à chaque requête.
 * - Si le token d'accès a expiré (12 h), le renouvelle une fois avec le token
 *   « refresh » (7 jours) puis relance la requête, sans redemander de code SMS.
 * - Transforme les erreurs de l'API en ApiError, plus simples à afficher.
 */

const TOKENS_KEY = 'nounou.tokens'

export interface Tokens {
  access: string
  refresh: string
}

/** Erreur renvoyée par l'API (statut HTTP + message lisible). */
export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown) {
    super(firstErrorMessage(data) ?? `Erreur ${status}`)
    this.status = status
    this.data = data
  }
}

/**
 * Extrait le premier message d'une réponse d'erreur de l'API, qui peut prendre
 * plusieurs formes : {"detail": "..."} ou {"phone": ["..."], "code": ["..."]}.
 */
export function firstErrorMessage(data: unknown): string | null {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) return data.length ? firstErrorMessage(data[0]) : null
  if (data && typeof data === 'object') {
    for (const value of Object.values(data)) {
      const message = firstErrorMessage(value)
      if (message) return message
    }
  }
  return null
}

// --- Stockage des tokens (dans le navigateur du téléphone) -----------------

export function loadTokens(): Tokens | null {
  try {
    const raw = localStorage.getItem(TOKENS_KEY)
    return raw ? (JSON.parse(raw) as Tokens) : null
  } catch {
    return null
  }
}

export function saveTokens(tokens: Tokens | null): void {
  try {
    if (tokens) localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens))
    else localStorage.removeItem(TOKENS_KEY)
  } catch {
    // Stockage indisponible : la connexion durera le temps de la visite
  }
}

// --- Requêtes ---------------------------------------------------------------

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

async function send(method: Method, path: string, body: unknown, access?: string): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  // Fichiers (FormData) : le navigateur choisit lui-même le format « multipart »
  const isForm = body instanceof FormData
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (access) headers.Authorization = `Bearer ${access}`
  return fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  })
}

async function parse(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

/** Renouvelle le token d'accès. Retourne les nouveaux tokens, ou null si la session a expiré. */
async function refreshTokens(tokens: Tokens): Promise<Tokens | null> {
  const response = await send('POST', '/api/token/refresh/', { refresh: tokens.refresh })
  if (!response.ok) return null
  const data = (await parse(response)) as Partial<Tokens>
  if (!data.access) return null
  // Le serveur renvoie aussi un nouveau refresh (rotation activée)
  const next = { access: data.access, refresh: data.refresh ?? tokens.refresh }
  saveTokens(next)
  return next
}

/** Appelé quand la session ne peut plus être renouvelée (déconnexion). */
let onSessionExpired: () => void = () => {}
export function setSessionExpiredHandler(handler: () => void): void {
  onSessionExpired = handler
}

export async function api<T>(method: Method, path: string, body?: unknown): Promise<T> {
  let tokens = loadTokens()
  let response = await send(method, path, body, tokens?.access)

  if (response.status === 401 && tokens) {
    tokens = await refreshTokens(tokens)
    if (tokens) {
      response = await send(method, path, body, tokens.access)
    } else {
      saveTokens(null)
      onSessionExpired()
    }
  }

  const data = await parse(response)
  if (!response.ok) throw new ApiError(response.status, data)
  return data as T
}

/** Télécharge un fichier protégé (ex : sa propre photo en attente) et renvoie une adresse locale. */
export async function apiBlobUrl(path: string): Promise<string> {
  let tokens = loadTokens()
  let response = await send('GET', path, undefined, tokens?.access)
  if (response.status === 401 && tokens) {
    tokens = await refreshTokens(tokens)
    if (tokens) response = await send('GET', path, undefined, tokens.access)
  }
  if (!response.ok) throw new ApiError(response.status, null)
  return URL.createObjectURL(await response.blob())
}
