import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../i18n/I18nContext'
import WithAside from './WithAside'

function setWidth(wide: boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: wide,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

function renderPage() {
  return render(
    <I18nProvider>
      <WithAside aside={<p>Colonne</p>}>
        <p>Contenu</p>
      </WithAside>
    </I18nProvider>,
  )
}

describe('WithAside', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it("n'ajoute rien sur téléphone ou tablette (la colonne n'est pas créée)", () => {
    setWidth(false)
    renderPage()
    expect(screen.getByText('Contenu')).toBeTruthy()
    expect(screen.queryByText('Colonne')).toBeNull()
    expect(screen.queryByRole('complementary')).toBeNull()
  })

  it('ajoute la colonne sur grand écran, nommée pour les lecteurs d’écran', () => {
    setWidth(true)
    renderPage()
    expect(screen.getByRole('complementary', { name: 'Informations complémentaires' })).toBeTruthy()
    expect(screen.getByText('Colonne')).toBeTruthy()
  })
})
