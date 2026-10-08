import { cleanup, render, screen } from '@testing-library/react'
import axe from 'axe-core'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from './auth/AuthContext'
import Layout from './components/Layout'
import { I18nProvider } from './i18n/I18nContext'
import ForgotPassword from './pages/ForgotPassword'
import Help from './pages/Help'
import Login from './pages/Login'
import Register from './pages/Register'
import Terms from './pages/Terms'
import Welcome from './pages/Welcome'

/**
 * Accessibilité des écrans publics (axe-core, règles WCAG 2.2 A/AA).
 * Le contraste des couleurs ne peut pas être mesuré ici (pas de vrai affichage) :
 * il est vérifié dans un navigateur (voir docs/DESIGN_SYSTEM.md).
 */
const SCREENS: [string, string, ReactNode][] = [
  ['accueil', '/', <Welcome />],
  ['connexion', '/connexion', <Login />],
  ['inscription', '/inscription', <Register />],
  ['mot de passe oublié', '/mot-de-passe-oublie', <ForgotPassword />],
  ['aide', '/aide', <Help />],
  ['conditions', '/conditions', <Terms />],
]

beforeEach(() => {
  localStorage.clear()
  // Seule la liste des moyens de connexion est demandée au serveur sur ces écrans
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify({ sms: true, google_client_id: '', apple_client_id: '' }), {
      headers: { 'Content-Type': 'application/json' },
    })),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('accessibilité des écrans publics', () => {
  it.each(SCREENS)('%s : aucune erreur WCAG détectée', async (_name, path, page) => {
    const { container } = render(
      <I18nProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={[path]}>
            <Layout>{page}</Layout>
          </MemoryRouter>
        </AuthProvider>
      </I18nProvider>,
    )
    await screen.findAllByRole('heading', { level: 1 })
    const results = await axe.run(container, {
      runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
      rules: { 'color-contrast': { enabled: false } },
    })
    const problems = results.violations.map((v) => `${v.id} : ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)
    expect(problems).toEqual([])
  })

  it('le lien « Aller au contenu » mène au contenu principal', async () => {
    render(
      <I18nProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/']}>
            <Layout>
              <Welcome />
            </Layout>
          </MemoryRouter>
        </AuthProvider>
      </I18nProvider>,
    )
    const skip = screen.getByRole('link', { name: /Aller au contenu|Skip to content/ })
    expect(skip.getAttribute('href')).toBe('#contenu')
    expect(document.getElementById('contenu')?.tagName).toBe('MAIN')
  })
})
