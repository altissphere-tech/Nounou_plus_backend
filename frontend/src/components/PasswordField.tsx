import { useId, useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

/** Mot de passe avec un bouton « œil » pour l'afficher (pratique sur téléphone). */
export default function PasswordField({
  label,
  value,
  onChange,
  hint,
  autoComplete = 'current-password',
}: {
  label: string
  value: string
  onChange: (value: string) => void
  hint?: string
  autoComplete?: 'current-password' | 'new-password'
}) {
  const { t } = useI18n()
  const [visible, setVisible] = useState(false)
  const id = useId()
  return (
    <div className="field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <div className="password-wrap">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          autoComplete={autoComplete}
          required
          minLength={autoComplete === 'new-password' ? 8 : undefined}
          aria-describedby={hint ? `${id}-hint` : undefined}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? t('password.hide') : t('password.show')}
          aria-pressed={visible}
        >
          {visible ? <EyeOff size={20} /> : <Eye size={20} />}
        </button>
      </div>
      {hint && (
        <span className="field-hint" id={`${id}-hint`}>
          {hint}
        </span>
      )}
    </div>
  )
}
