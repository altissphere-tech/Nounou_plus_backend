import { useI18n } from '../i18n/I18nContext'

/** Bas de liste : chargement, erreur ou bouton « Voir plus ». */
export default function ListFooter({
  loading,
  failed,
  hasMore,
  onMore,
}: {
  loading: boolean
  failed: boolean
  hasMore: boolean
  onMore: () => void
}) {
  const { t } = useI18n()
  if (failed) return <p className="error">{t('list.error')}</p>
  if (loading) return <p className="muted center">{t('common.loading')}</p>
  if (!hasMore) return null
  return (
    <button type="button" className="button secondary" onClick={onMore}>
      {t('list.more')}
    </button>
  )
}
