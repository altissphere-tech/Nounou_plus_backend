import { Briefcase, Check, Users } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

export type Role = 'client' | 'travailleur'

const ROLES = [
  { value: 'client', icon: Users, prefix: 'register.role.client' },
  { value: 'travailleur', icon: Briefcase, prefix: 'register.role.worker' },
] as const

/** Choix « Famille · Employeur » / « Professionnel(le) · Travailleur ». */
export default function RoleCards({ value, onChange }: { value: Role; onChange: (role: Role) => void }) {
  const { t } = useI18n()
  return (
    <fieldset className="roles">
      <legend className="field-label">{t('register.roleQuestion')}</legend>
      {ROLES.map((r) => (
        <label key={r.value} className={`role-option role-${r.value} ${value === r.value ? 'selected' : ''}`}>
          <input
            type="radio"
            name="role"
            value={r.value}
            checked={value === r.value}
            onChange={() => onChange(r.value)}
          />
          <span className="role-top">
            <span className="role-icon" aria-hidden="true">
              <r.icon size={20} />
            </span>
            <span className="role-tag">{t(`${r.prefix}.tag`)}</span>
          </span>
          <span className="role-title">{t(r.prefix)}</span>
          <span className="role-hint">{t(`${r.prefix}.hint`)}</span>
          <ul className="role-points">
            {(['p1', 'p2', 'p3'] as const).map((point) => (
              <li key={point}>
                <Check size={14} aria-hidden="true" /> {t(`${r.prefix}.${point}`)}
              </li>
            ))}
          </ul>
        </label>
      ))}
    </fieldset>
  )
}
