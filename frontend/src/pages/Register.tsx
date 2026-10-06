import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
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

  const roles: { value: Role; title: string; hint: string }[] = [
    { value: 'client', title: t('register.role.client'), hint: t('register.role.client.hint') },
    { value: 'travailleur', title: t('register.role.worker'), hint: t('register.role.worker.hint') },
  ]

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('register.title')}</h1>
      <fieldset className="roles">
        <legend className="field-label">{t('register.roleQuestion')}</legend>
        {roles.map((r) => (
          <label key={r.value} className={`role-option ${role === r.value ? 'selected' : ''}`}>
            <input
              type="radio"
              name="role"
              value={r.value}
              checked={role === r.value}
              onChange={() => setRole(r.value)}
            />
            <span className="role-title">{r.title}</span>
            <span className="role-hint">{r.hint}</span>
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
