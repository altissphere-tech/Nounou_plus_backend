import { useI18n } from '../i18n/I18nContext'
import { SERVICES } from '../profile/options'

/** Raccourcis « Tous / Nounou / Ménage / Cuisine » en haut des listes. */
export default function ServiceChips({ value, onChange }: { value: string; onChange: (service: string) => void }) {
  const { t } = useI18n()
  const options = [
    { slug: '', label: t('search.all') },
    ...SERVICES.map((slug) => ({ slug, label: t(`search.short.${slug}`) })),
  ]
  return (
    <div className="quick-chips" role="group" aria-label={t('search.quick')}>
      {options.map((option) => (
        <button
          key={option.slug}
          type="button"
          className={`quick-chip ${value === option.slug ? 'selected' : ''}`}
          aria-pressed={value === option.slug}
          onClick={() => onChange(option.slug)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
