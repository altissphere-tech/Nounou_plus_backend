import { useI18n } from '../i18n/I18nContext'
import { useOnline } from '../pwa/useOnline'

/** Bandeau affiché quand le téléphone n'a plus de connexion internet. */
export default function OfflineBanner() {
  const { t } = useI18n()
  const online = useOnline()
  if (online) return null
  return (
    <p className="offline-banner" role="status">
      📶 {t('offline.banner')}
    </p>
  )
}
