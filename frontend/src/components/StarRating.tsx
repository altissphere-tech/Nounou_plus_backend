import { useI18n } from '../i18n/I18nContext'

/** Note de 1 à 5 étoiles, utilisable au doigt et au clavier (groupe de boutons radio). */
export default function StarRating({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  const { t } = useI18n()
  return (
    <fieldset className="stars">
      <legend className="field-label">{label}</legend>
      <div className="stars-row">
        {[1, 2, 3, 4, 5].map((n) => (
          <label key={n} className={`star ${n <= value ? 'on' : ''}`}>
            <input
              type="radio"
              name={label}
              value={n}
              checked={value === n}
              onChange={() => onChange(n)}
              aria-label={t('review.stars', { count: String(n) })}
            />
            ★
          </label>
        ))}
      </div>
    </fieldset>
  )
}
