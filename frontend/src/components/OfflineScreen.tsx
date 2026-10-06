import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'

/** Utilisateur connecté mais sans internet : on garde sa session et on propose de réessayer. */
export default function OfflineScreen() {
  const { t } = useI18n()
  const { reload } = useAuth()
  return (
    <div className="card center">
      <p className="offline-icon" aria-hidden="true">
        📶
      </p>
      <h1>{t('offline.title')}</h1>
      <p className="muted">{t('offline.text')}</p>
      <button type="button" className="button primary" onClick={() => void reload()}>
        {t('offline.retry')}
      </button>
    </div>
  )
}
