import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { confirmEmail } from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'

/** Page ouverte depuis le lien reçu par e-mail : confirme l'adresse. */
export default function ConfirmEmail() {
  const { t } = useI18n()
  const { user, reload } = useAuth()
  const token = useSearchParams()[0].get('token') ?? ''
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')

  useEffect(() => {
    confirmEmail(token).then(
      () => {
        setState('ok')
        void reload()
      },
      () => setState('error'),
    )
  }, [token, reload])

  return (
    <div className="card auth-card">
      <h1>{t('confirmEmail.title')}</h1>
      {state === 'loading' && <p className="muted">{t('common.loading')}</p>}
      {state === 'ok' && <p className="info-banner" role="status">✔ {t('confirmEmail.ok')}</p>}
      {state === 'error' && <p className="error" role="alert">{t('confirmEmail.error')}</p>}
      <Link to={user ? '/accueil' : '/connexion'} className="button primary">
        {user ? t('confirmEmail.continue') : t('reset.login')}
      </Link>
    </div>
  )
}
