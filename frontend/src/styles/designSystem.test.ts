// @vitest-environment node
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

/**
 * Garde-fous du design system : les couleurs ne s'écrivent que dans tokens.css,
 * et chaque fichier de style est bien chargé par styles.css.
 */
const dir = fileURLToPath(new URL('.', import.meta.url))
const files = readdirSync(dir).filter((name) => name.endsWith('.css'))
const read = (name: string) => readFileSync(dir + name, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '')

describe('design system', () => {
  it.each(files.filter((name) => name !== 'tokens.css'))('%s utilise les couleurs du design system', (name) => {
    const raw = read(name).match(/#[0-9a-f]{3,8}\b|rgba?\(/gi) ?? []
    expect(raw, `couleur écrite en dur dans ${name} : ajoutez-la à tokens.css`).toEqual([])
  })

  it('chaque fichier de style est importé une fois dans styles.css', () => {
    const index = readFileSync(dir + '../styles.css', 'utf8')
    for (const name of files) {
      expect(index.split(`'./styles/${name}'`).length - 1, name).toBe(1)
    }
  })
})
