import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { requestCode } from '../api/accounts'
import { errorText } from '../components/errors'
import PhoneField from '../components/PhoneField'
import { useI18n } from '../i18n/I18nContext'

export default function Login() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      await requestCode(phone)
      navigate('/code', { state: { phone } })
    } catch (err) {
      setError(errorText(err, lang, t, 'login.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('login.title')}</h1>
      <PhoneField value={phone} onChange={setPhone} />
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : t('login.submit')}
      </button>
      <Link to="/inscription" className="link">
        {t('login.noAccount')}
      </Link>
    </form>
  )
}
