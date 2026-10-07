import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, firstErrorMessage, loadTokens, revokeSession, saveTokens } from './client'

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

afterEach(() => {
  vi.restoreAllMocks()
  saveTokens(null)
})

describe("messages d'erreur de l'API", () => {
  it('lit le format {"detail": ...}', () => {
    expect(firstErrorMessage({ detail: 'Introuvable.' })).toBe('Introuvable.')
  })

  it('lit le format par champ {"phone": [...]}', () => {
    expect(firstErrorMessage({ phone: ['Numéro invalide.'] })).toBe('Numéro invalide.')
  })
})

describe('client API', () => {
  it('envoie le token de connexion', async () => {
    saveTokens({ access: 'A1', refresh: 'R1' })
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(200, { ok: true }))
    await api('GET', '/api/accounts/me/')
    const headers = fetchMock.mock.calls[0][1]!.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer A1')
  })

  it('renouvelle le token expiré puis relance la requête', async () => {
    saveTokens({ access: 'expiré', refresh: 'R1' })
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expiré' }))
      .mockResolvedValueOnce(jsonResponse(200, { access: 'A2', refresh: 'R2' }))
      .mockResolvedValueOnce(jsonResponse(200, { id: 1 }))
    await expect(api('GET', '/api/accounts/me/')).resolves.toEqual({ id: 1 })
    expect(fetchMock.mock.calls[1][0]).toBe('/api/token/refresh/')
    expect(loadTokens()).toEqual({ access: 'A2', refresh: 'R2' })
  })

  it('un seul renouvellement pour plusieurs requêtes expirées en même temps', async () => {
    saveTokens({ access: 'expiré', refresh: 'R1' })
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
      if (url === '/api/token/refresh/') return jsonResponse(200, { access: 'A2', refresh: 'R2' })
      const auth = (init!.headers as Record<string, string>).Authorization
      return auth === 'Bearer A2' ? jsonResponse(200, { ok: true }) : jsonResponse(401, { detail: 'expiré' })
    })
    await Promise.all([api('GET', '/api/a/'), api('GET', '/api/b/'), api('GET', '/api/c/')])
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => url === '/api/token/refresh/')
    expect(refreshCalls).toHaveLength(1) // un refresh ne sert qu'une fois côté serveur
    expect(loadTokens()).toEqual({ access: 'A2', refresh: 'R2' })
  })

  it('la déconnexion demande au serveur de révoquer le refresh', () => {
    saveTokens({ access: 'A1', refresh: 'R1' })
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(200, {}))
    revokeSession()
    expect(loadTokens()).toBeNull()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/accounts/logout/')
    expect(JSON.parse(fetchMock.mock.calls[0][1]!.body as string)).toEqual({ refresh: 'R1' })
  })

  it('déconnecte si le renouvellement échoue', async () => {
    saveTokens({ access: 'expiré', refresh: 'expiré' })
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expiré' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'refresh expiré' }))
    await expect(api('GET', '/api/accounts/me/')).rejects.toBeInstanceOf(ApiError)
    expect(loadTokens()).toBeNull()
  })

  it('envoie les fichiers en multipart, sans forcer le Content-Type', async () => {
    saveTokens({ access: 'A1', refresh: 'R1' })
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(201, { ok: true }))
    const form = new FormData()
    form.append('doc_type', 'identite')
    await api('POST', '/api/verification/documents/', form)
    const init = fetchMock.mock.calls[0][1]!
    expect(init.body).toBe(form)
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined()
  })
})
