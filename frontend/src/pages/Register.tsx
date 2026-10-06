import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Briefcase, Check, Users } from 'lucide-react'
import { register } from '../api/accounts'
import { errorText } from '../components/errors'
import PhoneField from '../components/PhoneField'
import { useI18n } from '../i18n/I18nContext'

type Role = 'client' | 'travailleur'

export default function Register() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const [role, setRole] = useState<Role>('client')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(phone, role)
      navigate('/code', { state: { phone } })
    } catch (err) {
      setError(errorText(err, lang, t, 'register.error'))
    } finally {
      setBusy(false)
    }
  }

  const roles = [
    { value: 'client', icon: Users, prefix: 'register.role.client' },
    { value: 'travailleur', icon: Briefcase, prefix: 'register.role.worker' },
  ] as const

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('register.title')}</h1>
      <fieldset className="roles">
        <legend className="field-label">{t('register.roleQuestion')}</legend>
        {roles.map((r) => (
          <label key={r.value} className={`role-option role-${r.value} ${role === r.value ? 'selected' : ''}`}>
            <input
              type="radio"
              name="role"
              value={r.value}
              checked={role === r.value}
              onChange={() => setRole(r.value)}
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
      <PhoneField value={phone} onChange={setPhone} />
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : t('register.submit')}
      </button>
      <Link to="/connexion" className="link">
        {t('register.haveAccount')}
      </Link>
    </form>
  )
}
