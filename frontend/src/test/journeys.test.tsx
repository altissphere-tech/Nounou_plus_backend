import { cleanup, configure, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { saveTokens } from '../api/client'
import { TOKENS, fakeServer, page, user, worker } from './fakeServer'

/**
 * Parcours clés, tels qu'un utilisateur les vit (clics et saisies dans les vrais
 * écrans), avec un faux serveur. Voir docs/PARCOURS.md.
 */
function openApp(path: string) {
  window.history.pushState({}, '', path)
  render(<App />)
}

// Les écrans sont téléchargés à la demande : on leur laisse le temps d'arriver
configure({ asyncUtilTimeout: 5000 })
vi.setConfig({ testTimeout: 20000 })

const COMMON = {
  'GET /api/accounts/auth-options/': { sms: true, google_client_id: '', apple_client_id: '' },
  'GET /api/notifications/unread-count/': { unread: 0 },
  'GET /api/favorites/': { workers: [], jobs: [] },
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('nounou.lang', 'fr')
})

afterEach(() => {
  cleanup()
  saveTokens(null)
  vi.unstubAllGlobals()
})

describe('parcours : inscription', () => {
  it('famille par téléphone : rôle, numéro, code SMS, puis accueil', async () => {
    const server = fakeServer({
      ...COMMON,
      'POST /api/accounts/register/': [201, { message: 'Un code a été envoyé.' }],
      'POST /api/accounts/otp/verify/': { message: 'Connexion réussie.', tokens: TOKENS, user: user() },
      'GET /api/accounts/me/': user(),
    })
    const person = userEvent.setup()
    openApp('/inscription')

    await person.click(await screen.findByText('Une famille'))
    await person.type(screen.getByLabelText('Numéro de téléphone'), '0812300001')
    await person.click(screen.getByRole('button', { name: 'Recevoir mon code' }))

    await screen.findByRole('heading', { name: 'Entrez votre code' })
    expect(server.sent('POST /api/accounts/register/')[0]).toMatchObject({ role: 'client' })
    await person.type(screen.getByLabelText('Code à 6 chiffres'), '123456')
    await person.click(screen.getByRole('button', { name: 'Valider' }))

    expect(await screen.findByRole('heading', { name: 'Bonjour !' })).toBeTruthy()
    expect(server.sent('POST /api/accounts/otp/verify/')[0]).toMatchObject({ code: '123456' })
  })

  it("avec e-mail : le code SMS d'abord, puis mot de passe et adresse enregistrés", async () => {
    let me = user()
    const server = fakeServer({
      ...COMMON,
      'POST /api/accounts/register/': [201, { message: 'Un code a été envoyé.' }],
      'POST /api/accounts/otp/verify/': { message: 'Connexion réussie.', tokens: TOKENS, user: me },
      'POST /api/accounts/password/change/': () => {
        me = { ...me, has_password: true }
        return { message: 'ok', tokens: TOKENS, user: me }
      },
      'POST /api/accounts/email/': (body: unknown) => {
        me = { ...me, pending_email: (body as { email: string }).email }
        return { message: 'ok', user: me }
      },
      'GET /api/accounts/me/': () => me,
    })
    const person = userEvent.setup()
    openApp('/inscription')

    await person.click(await screen.findByRole('radio', { name: /E-mail/ }))
    await person.type(screen.getByLabelText('Adresse e-mail'), 'marie@example.com')
    await person.type(screen.getByLabelText('Mot de passe'), 'Lubumbashi2026')
    await person.type(screen.getByLabelText('Numéro de téléphone'), '0812300001')
    await person.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    // Aucun compte utilisable sans le code SMS ; e-mail et mot de passe ne partent pas à l'inscription
    await screen.findByRole('heading', { name: 'Entrez votre code' })
    expect(server.sent('POST /api/accounts/register/')[0]).not.toHaveProperty('password')
    await person.type(screen.getByLabelText('Code à 6 chiffres'), '123456')
    await person.click(screen.getByRole('button', { name: 'Valider' }))

    expect(await screen.findByText('Confirmez votre adresse e-mail')).toBeTruthy()
    expect(server.sent('POST /api/accounts/password/change/')).toEqual([{ new_password: 'Lubumbashi2026' }])
    expect(server.sent('POST /api/accounts/email/')).toEqual([
      { email: 'marie@example.com', current_password: 'Lubumbashi2026' },
    ])
  })
})

describe('parcours : connexion', () => {
  it('par e-mail avec un numéro jamais confirmé : le code SMS est demandé', async () => {
    fakeServer({
      ...COMMON,
      'POST /api/accounts/login/': [
        400,
        { detail: 'Confirmez votre numéro.', phone_verification_required: true, phone: '+243812300001' },
      ],
    })
    const person = userEvent.setup()
    openApp('/connexion')

    await person.click(await screen.findByRole('radio', { name: /E-mail/ }))
    await person.type(screen.getByLabelText('Adresse e-mail'), 'marie@example.com')
    await person.type(screen.getByLabelText('Mot de passe'), 'Lubumbashi2026')
    await person.click(screen.getByRole('button', { name: 'Se connecter' }))

    expect(await screen.findByText('Code envoyé au +243812300001')).toBeTruthy()
  })
})

describe('parcours : mise en relation', () => {
  it("famille : fiche d'une nounou, intérêt envoyé, coordonnées toujours cachées", async () => {
    saveTokens(TOKENS)
    const server = fakeServer({
      ...COMMON,
      'GET /api/accounts/me/': user(),
      'GET /api/workers/7/': worker(),
      'GET /api/reviews/workers/7/': { summary: { count: 0, average: null, criteria: {} }, ...page([]) },
      'POST /api/matches/interest/': [201, { message: 'Votre intérêt a été enregistré.', match: { id: 3 } }],
    })
    const person = userEvent.setup()
    openApp('/travailleurs/7')

    expect(await screen.findByRole('heading', { name: 'Grâce M.' })).toBeTruthy()
    expect(screen.queryByText(/812300002/)).toBeNull()
    await person.click(screen.getByRole('button', { name: 'Je suis intéressé(e)' }))

    await waitFor(() => expect(server.sent('POST /api/matches/interest/')).toEqual([{ profile_id: 7 }]))
    expect(await screen.findByRole('status')).toBeTruthy()
  })

  it('travailleur pas encore vérifié : les annonces des familles restent cachées', async () => {
    saveTokens(TOKENS)
    fakeServer({
      ...COMMON,
      'GET /api/accounts/me/': user({ role: 'travailleur' }),
      'GET /api/jobs/': [403, { detail: 'Profil à vérifier.' }],
    })
    openApp('/annonces')

    expect(await screen.findByText(/visibles une fois votre profil vérifié/)).toBeTruthy()
    expect(screen.queryByText(/Impossible de charger/)).toBeNull()
  })
})
