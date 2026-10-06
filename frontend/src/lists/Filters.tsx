import { useState } from 'react'
import type { FormEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'
import { AVAILABILITIES, SERVICES } from '../profile/options'

export type FilterValues = Record<string, string>

export interface FilterDefinition {
  name: string
  label: TranslationKey
  kind: 'service' | 'availability' | 'text' | 'number' | 'ordering'
  placeholder?: TranslationKey
  options?: string[] // pour le tri
}

/**
 * Panneau de filtres repliable. Les valeurs sont gardées dans l'adresse de la page :
 * en revenant d'une fiche, la recherche est conservée.
 */
export default function Filters({
  definitions,
  values,
  onApply,
}: {
  definitions: FilterDefinition[]
  values: FilterValues
  onApply: (values: FilterValues) => void
}) {
  const { t } = useI18n()
  const [draft, setDraft] = useState<FilterValues>(values)
  const active = Object.values(values).filter(Boolean).length

  function submit(event: FormEvent) {
    event.preventDefault()
    onApply(draft)
  }

  function reset() {
    setDraft({})
    onApply({})
  }

  const set = (name: string, value: string) => setDraft((current) => ({ ...current, [name]: value }))

  return (
    <details className="card filters">
      <summary>
        {t('filters.title')}
        {active > 0 && <span className="filters-count">{active}</span>}
      </summary>
      <form onSubmit={submit} className="filters-form">
        {definitions.map((def) => {
          const id = `filter-${def.name}`
          const value = draft[def.name] ?? ''
          let input
          if (def.kind === 'service' || def.kind === 'availability' || def.kind === 'ordering') {
            const options =
              def.kind === 'service' ? SERVICES : def.kind === 'availability' ? AVAILABILITIES : def.options!
            const prefix = def.kind === 'service' ? 'service' : def.kind === 'availability' ? 'availability' : 'ordering'
            input = (
              <select id={id} value={value} onChange={(e) => set(def.name, e.target.value)}>
                {def.kind !== 'ordering' && (
                  <option value="">
                    {t(def.kind === 'service' ? 'filters.service.any' : 'filters.availability.any')}
                  </option>
                )}
                {options.map((option) => (
                  <option key={option} value={option}>
                    {t(`${prefix}.${option}` as TranslationKey)}
                  </option>
                ))}
              </select>
            )
          } else {
            input = (
              <input
                id={id}
                type={def.kind === 'number' ? 'number' : 'text'}
                inputMode={def.kind === 'number' ? 'decimal' : undefined}
                min={def.kind === 'number' ? 0 : undefined}
                placeholder={def.placeholder ? t(def.placeholder) : undefined}
                value={value}
                onChange={(e) => set(def.name, e.target.value)}
              />
            )
          }
          return (
            <div key={def.name} className="field">
              <label className="field-label" htmlFor={id}>
                {t(def.label)}
              </label>
              {input}
            </div>
          )
        })}
        <button type="submit" className="button primary">
          {t('filters.apply')}
        </button>
        {active > 0 && (
          <button type="button" className="link" onClick={reset}>
            {t('filters.reset')}
          </button>
        )}
      </form>
    </details>
  )
}

/** Lit les filtres présents dans l'adresse (?service=…&location=…). */
export function filtersFromParams(params: URLSearchParams, names: string[]): FilterValues {
  const values: FilterValues = {}
  for (const name of names) {
    const value = params.get(name)
    if (value) values[name] = value
  }
  return values
}
