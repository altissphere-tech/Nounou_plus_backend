import { useI18n } from '../i18n/I18nContext'
import { CardSkeleton, Skeleton } from './Skeleton'

/** Écran en cours de téléchargement : en-tête violet et deux cartes en silhouette. */
export default function PageSkeleton() {
  const { t } = useI18n()
  return (
    <section className="stack" role="status">
      <span className="visually-hidden">{t('common.loading')}</span>
      <div className="page-head skeleton-head" aria-hidden="true">
        <Skeleton width="60%" height={28} />
      </div>
      <CardSkeleton />
      <CardSkeleton />
    </section>
  )
}
