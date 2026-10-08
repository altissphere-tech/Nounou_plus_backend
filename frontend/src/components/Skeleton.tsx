import { useI18n } from '../i18n/I18nContext'

/**
 * Silhouettes grises affichées pendant un chargement : l'écran garde sa forme,
 * ce qui paraît plus rapide qu'un simple « Chargement… ». Les lecteurs d'écran
 * entendent seulement « Chargement… ».
 */
export function Skeleton({ width, height = 14, round = false }: { width?: number | string; height?: number; round?: boolean }) {
  return <span className={round ? 'skeleton round' : 'skeleton'} style={{ width, height }} aria-hidden="true" />
}

/** Une carte de résultat (profil ou annonce) en cours de chargement. */
export function CardSkeleton() {
  return (
    <div className="card result skeleton-card" aria-hidden="true">
      <div className="skeleton-row">
        <Skeleton width={52} height={52} round />
        <div className="skeleton-lines">
          <Skeleton width="55%" height={16} />
          <Skeleton width="80%" />
        </div>
      </div>
      <Skeleton width="40%" height={24} />
      <Skeleton width="65%" />
    </div>
  )
}

/** Liste de résultats en cours de chargement. */
export function ListSkeleton({ count = 3 }: { count?: number }) {
  const { t } = useI18n()
  return (
    <div className="card-grid" role="status">
      <span className="visually-hidden">{t('common.loading')}</span>
      {Array.from({ length: count }, (_, index) => (
        <CardSkeleton key={index} />
      ))}
    </div>
  )
}
