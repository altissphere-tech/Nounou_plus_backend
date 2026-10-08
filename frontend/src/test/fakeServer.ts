import { vi } from 'vitest'

/**
 * Faux serveur pour les tests d'écrans : chaque appel de l'application
 * (« POST /api/accounts/register/ ») est servi par une fonction du test,
 * et tous les appels sont notés pour pouvoir les vérifier.
 */
/** Réponse fixe, ou fonction qui la calcule ; [statut, données] pour un statut autre que 200. */
export type Handler = ((body: unknown) => unknown) | unknown

export interface Call {
  method: string
  path: string
  body: unknown
}

export function fakeServer(routes: Record<string, Handler>) {
  const calls: Call[] = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost')
    const method = (init?.method ?? 'GET').toUpperCase()
    const body = typeof init?.body === 'string' ? JSON.parse(init.body) : init?.body ?? null
    calls.push({ method, path: url.pathname, body })
    const handler = routes[`${method} ${url.pathname}`]
    const result =
      handler === undefined
        ? [404, { detail: 'Introuvable.' }]
        : typeof handler === 'function'
          ? (handler as (body: unknown) => unknown)(body)
          : handler
    const [status, data] = Array.isArray(result) && typeof result[0] === 'number' ? result : [200, result]
    return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fetchMock)
  return {
    calls,
    /** Corps envoyés à une adresse donnée (« POST /api/... »). */
    sent: (route: string) => calls.filter((c) => `${c.method} ${c.path}` === route).map((c) => c.body),
  }
}

export const TOKENS = { access: 'jeton-acces', refresh: 'jeton-renouvellement' }

export function user(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    phone: '+243812300001',
    role: 'client',
    phone_verified: true,
    email: null,
    email_verified: false,
    pending_email: '',
    has_password: false,
    social_providers: [],
    photo_status: 'aucune',
    photo_rejection_reason: '',
    created_at: '2026-10-01T10:00:00Z',
    warnings: [],
    ...overrides,
  }
}

export function worker(overrides: Record<string, unknown> = {}) {
  return {
    id: 7,
    first_name: 'Grâce',
    last_name: 'M.',
    photo_url: null,
    bio: 'Douce et patiente.',
    services_list: ['nounou'],
    years_experience: 5,
    availability: 'temps_plein',
    expected_salary: '250000',
    location: 'Kenya',
    is_verified: true,
    trust: { phone: true, identity: true, references: false },
    rating: { average: null, count: 0 },
    phone_display: '+2438*******2',
    ...overrides,
  }
}

export const page = <T>(results: T[]) => ({ count: results.length, next: null, previous: null, results })
