import { useSearchParams } from 'react-router-dom'
import { searchJobs } from '../api/search'
import type { PublicJob } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import PageHead from '../components/PageHead'
import ServiceChips from '../lists/ServiceChips'
import { JobCard } from '../lists/cards'
import Filters, { filtersFromParams } from '../lists/Filters'
import type { FilterDefinition, FilterValues } from '../lists/Filters'
import ListFooter from '../lists/ListFooter'
import { usePagedList } from '../lists/usePagedList'

const FILTERS: FilterDefinition[] = [
  { name: 'service', label: 'filters.service', kind: 'service' },
  { name: 'location', label: 'filters.location', kind: 'text', placeholder: 'filters.location.placeholder' },
  { name: 'availability', label: 'filters.availability', kind: 'availability' },
  { name: 'min_budget', label: 'filters.minBudget', kind: 'number' },
]

/** Annonces ouvertes des familles (travailleurs). */
export default function Jobs() {
  const { t } = useI18n()
  const [params, setParams] = useSearchParams()
  const filters = filtersFromParams(params, FILTERS.map((f) => f.name))
  const list = usePagedList<PublicJob>(() => searchJobs(filters), params.toString())

  return (
    <section className="stack">
      <PageHead title={t('jobs.title')}>
        <ServiceChips value={filters.service ?? ''} onChange={(service) => setParams({ ...filters, service })} />
      </PageHead>
      <Filters
        key={params.toString()}
        definitions={FILTERS}
        values={filters}
        onApply={(values: FilterValues) => setParams(values)}
      />
      {!list.loading && !list.failed && <p className="list-count">{t('list.count', { count: String(list.count) })}</p>}
      {!list.loading && !list.failed && list.count === 0 && <p className="card muted">{t('jobs.empty')}</p>}
      <div className="card-grid">
        {list.items.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
      <ListFooter loading={list.loading} failed={list.failed} hasMore={list.hasMore} onMore={list.loadMore} />
    </section>
  )
}
