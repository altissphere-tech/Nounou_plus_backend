import { describe, expect, it } from 'vitest'
import en from './en'
import fr from './fr'
import { interpolate } from './interpolate'

describe('traductions', () => {
  it('chaque texte français existe en anglais, et inversement', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(fr).sort())
  })

  it("aucun texte n'est vide", () => {
    for (const dictionary of [fr, en]) {
      for (const [key, value] of Object.entries(dictionary)) {
        expect(value.trim(), key).not.toBe('')
      }
    }
  })

  it('les variables {…} sont les mêmes dans les deux langues', () => {
    const variables = (text: string) => (text.match(/\{\w+\}/g) ?? []).sort()
    for (const key of Object.keys(fr) as (keyof typeof fr)[]) {
      expect(variables(en[key]), key).toEqual(variables(fr[key]))
    }
  })

  it('remplace les variables', () => {
    expect(interpolate('Code envoyé au {phone}', { phone: '+243' })).toBe('Code envoyé au +243')
  })
})
