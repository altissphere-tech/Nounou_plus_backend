import { useSearchParams } from 'react-router-dom'
import { searchWorkers } from '../api/search'
import type { PublicWorker } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import { WorkerCard } from '../lists/cards'
import Filters, { filtersFromParams } from '../lists/Filters'
import type { FilterDefinition, FilterValues } from '../lists/Filters'
import ListFooter from '../lists/ListFooter'
import { usePagedList } from '../lists/usePagedList'

const FILTERS: FilterDefinition[] = [
  { name: 'service', label: 'filters.service', kind: 'service' },
  { name: 'location', label: 'filters.location', kind: 'text', placeholder: 'filters.location.placeholder' },
  { name: 'availability', label: 'filters.availability', kind: 'availability' },
  { name: 'max_salary', label: 'filters.maxSalary', kind: 'number' },
  { name: 'min_experience', label: 'filters.minExperience', kind: 'number' },
  {
    name: 'ordering',
    label: 'filters.ordering',
    kind: 'ordering',
    options: ['recent', 'rating', 'salary', 'experience'],
  },
]

/** Recherche de travailleurs vérifiés (familles). */
export default function Search() {
  const { t } = useI18n()
  const [params, setParams] = useSearchParams()
  const filters = filtersFromParams(params, FILTERS.map((f) => f.name))
  const list = usePagedList<PublicWorker>(() => searchWorkers(filters), params.toString())

  return (
    <section className="stack">
      <h1>{t('search.title')}</h1>
      <Filters
        key={params.toString()}
        definitions={FILTERS}
        values={filters}
        onApply={(values: FilterValues) => setParams(values)}
      />
      {!list.loading && !list.failed && <p className="muted">{t('list.count', { count: String(list.count) })}</p>}
      {!list.loading && !list.failed && list.count === 0 && <p className="card muted">{t('search.empty')}</p>}
      {list.items.map((worker) => (
        <WorkerCard key={worker.id} worker={worker} />
      ))}
      <ListFooter loading={list.loading} failed={list.failed} hasMore={list.hasMore} onMore={list.loadMore} />
    </section>
  )
}
