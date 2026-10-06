import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/client'
import en from '../i18n/en'
import fr from '../i18n/fr'
import type { TranslationKey } from '../i18n/fr'
import { errorText } from './errors'

const tFr = (key: TranslationKey) => fr[key]
const tEn = (key: TranslationKey) => en[key]

describe("messages d'erreur affichés", () => {
  it('erreur de saisie : message précis du serveur en français', () => {
    const error = new ApiError(400, { phone: ['Un compte existe déjà avec ce numéro de téléphone.'] })
    expect(errorText(error, 'fr', tFr, 'register.error')).toBe('Un compte existe déjà avec ce numéro de téléphone.')
  })

  it('erreur de saisie en anglais : message traduit', () => {
    const error = new ApiError(400, { phone: ['Un compte existe déjà avec ce numéro de téléphone.'] })
    expect(errorText(error, 'en', tEn, 'register.error')).toBe(en['register.error'])
  })

  it('serveur injoignable alors qu\'internet fonctionne : « le serveur ne répond pas »', () => {
    const text = errorText(new TypeError('Failed to fetch'), 'fr', tFr, 'register.error', { online: true, dev: false })
    expect(text).toBe(fr['common.serverDown'])
  })

  it('en développement, rappel de lancer Django', () => {
    const text = errorText(new TypeError('Failed to fetch'), 'fr', tFr, 'register.error', { online: true, dev: true })
    expect(text).toContain('python manage.py runserver')
  })

  it('téléphone sans internet : « vérifiez votre connexion »', () => {
    const text = errorText(new TypeError('Failed to fetch'), 'fr', tFr, 'register.error', { online: false, dev: false })
    expect(text).toBe(fr['common.networkError'])
  })

  it('erreur 500 du serveur : « le serveur ne répond pas »', () => {
    expect(errorText(new ApiError(500, null), 'fr', tFr, 'register.error', { dev: false })).toBe(fr['common.serverDown'])
  })
})
