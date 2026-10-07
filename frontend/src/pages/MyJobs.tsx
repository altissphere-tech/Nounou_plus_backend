import { useState } from 'react'
import { Link } from 'react-router-dom'
import { myJobs, updateJob } from '../api/search'
import type { MyJob } from '../api/types'
import { useI18n } from '../i18n/I18nContext'
import PageHead from '../components/PageHead'
import { MyJobCard } from '../lists/cards'
import ListFooter from '../lists/ListFooter'
import { usePagedList } from '../lists/usePagedList'

/** Annonces publiées par la famille, avec changement de statut. */
export default function MyJobs() {
  const { t } = useI18n()
  const [version, setVersion] = useState(0)
  const list = usePagedList<MyJob>(myJobs, String(version))

  async function changeStatus(job: MyJob, status: MyJob['status']) {
    await updateJob(job.id, { status })
    setVersion((v) => v + 1)
  }

  return (
    <section className="stack">
      <PageHead title={t('myJobs.title')} />
      <Link to="/mes-annonces/nouvelle" className="button dashed">
        + {t('myJobs.new')}
      </Link>
      {!list.loading && !list.failed && list.count === 0 && <p className="card muted">{t('myJobs.empty')}</p>}
      <div className="card-grid">
        {list.items.map((job) => (
          <MyJobCard key={job.id} job={job} onStatus={(status) => changeStatus(job, status)} />
        ))}
      </div>
      <ListFooter loading={list.loading} failed={list.failed} hasMore={list.hasMore} onMore={list.loadMore} />
    </section>
  )
}
