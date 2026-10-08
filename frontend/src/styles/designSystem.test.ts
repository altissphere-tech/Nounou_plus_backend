// @vitest-environment node
/// <reference types="node" />
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

/**
 * Garde-fous du design system : les couleurs ne s'écrivent que dans tokens.css,
 * et chaque fichier de style est bien chargé par styles.css.
 */
const dir = fileURLToPath(new URL('.', import.meta.url))
const files: string[] = readdirSync(dir).filter((name: string) => name.endsWith('.css'))
const read = (path: string): string => readFileSync(path, 'utf8')
const withoutComments = (css: string) => css.replace(/\/\*[\s\S]*?\*\//g, '')

describe('design system', () => {
  it('les fichiers de style sont bien lus', () => {
    expect(files.length).toBeGreaterThan(10)
    expect(read(dir + 'tokens.css')).toContain('--brand:')
  })

  it.each(files.filter((name) => name !== 'tokens.css'))('%s utilise les couleurs du design system', (name: string) => {
    const raw = withoutComments(read(dir + name)).match(/#[0-9a-f]{3,8}\b|rgba?\(/gi) ?? []
    expect(raw, `couleur écrite en dur dans ${name} : ajoutez-la à tokens.css`).toEqual([])
  })

  it('chaque fichier de style est importé une fois dans styles.css', () => {
    const index = read(dir + '../styles.css')
    for (const name of files) {
      expect(index.split(`'./styles/${name}'`).length - 1, name).toBe(1)
    }
  })
})
