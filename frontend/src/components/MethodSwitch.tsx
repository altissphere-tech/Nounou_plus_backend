import { Mail, Smartphone } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

export type Method = 'email' | 'phone'

/** Choix « E-mail / Téléphone » pour se connecter ou s'inscrire. */
export default function MethodSwitch({ value, onChange }: { value: Method; onChange: (method: Method) => void }) {
  const { t } = useI18n()
  const options = [
    { value: 'phone', icon: Smartphone, label: t('method.phone') },
    { value: 'email', icon: Mail, label: t('method.email') },
  ] as const
  return (
    <div className="segmented small" role="radiogroup" aria-label={t('method.label')}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          className={value === option.value ? 'active' : ''}
          onClick={() => onChange(option.value)}
        >
          <option.icon size={16} aria-hidden="true" /> {option.label}
        </button>
      ))}
    </div>
  )
}
