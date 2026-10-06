import { describe, expect, it } from 'vitest'
import { money } from './format'

describe('montants en francs congolais', () => {
  it('sépare les milliers et ajoute FC', () => {
    // fr-FR utilise une espace fine insécable comme séparateur des milliers
    expect(money('250000.00', 'fr').replace(/\s/g, ' ')).toBe('250 000 FC')
    expect(money('250000.00', 'en')).toBe('250,000 FC')
  })

  it('ignore les centimes', () => {
    expect(money('1500.50', 'en')).toBe('1,501 FC')
  })
})
