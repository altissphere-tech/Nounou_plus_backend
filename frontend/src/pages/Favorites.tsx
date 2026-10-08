import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listFavorites } from '../api/favorites'
import type { Favorites as FavoritesData } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import PageHead from '../components/PageHead'
import { useI18n } from '../i18n/I18nContext'
import { JobCard, WorkerCard } from '../lists/cards'
import { useFavoriteIds } from '../lists/favorites'
import { ListSkeleton } from '../components/Skeleton'

/** Profils (familles) ou annonces (travailleurs) mis de côté avec le cœur. */
export default function Favorites() {
  const { t } = useI18n()
  const { user } = useAuth()
  const isClient = user!.role === 'client'
  const [data, setData] = useState<FavoritesData | null | undefined>(undefined)
  // Retirer un cœur ici fait disparaître la carte
  const ids = useFavoriteIds(isClient ? 'workers' : 'jobs', user!.id)

  useEffect(() => {
    listFavorites().then(setData, () => setData(null))
  }, [])

  const workers = data?.workers.filter((w) => !ids || ids.has(w.id)) ?? []
  const jobs = data?.jobs.filter((j) => !ids || ids.has(j.id)) ?? []
  const empty = data && workers.length === 0 && jobs.length === 0

  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={t('favorites.title')} />
      {data === undefined && <ListSkeleton count={2} />}
      {data === null && <p className="error">{t('list.error')}</p>}
      {empty && (
        <div className="card">
          <p>{isClient ? t('favorites.empty.client') : t('favorites.empty.worker')}</p>
          <Link to={isClient ? '/recherche' : '/annonces'} className="button primary">
            {isClient ? t('nav.search') : t('nav.jobs')}
          </Link>
        </div>
      )}
      <div className="card-grid">
        {workers.map((worker) => (
          <WorkerCard key={worker.id} worker={worker} />
        ))}
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
    </section>
  )
}
