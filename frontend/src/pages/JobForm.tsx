import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { createJob, getJob, updateJob } from '../api/search'
import type { Availability, JobInput, MyJob, ServiceSlug } from '../api/types'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import { useI18n } from '../i18n/I18nContext'
import { AVAILABILITIES, SERVICES } from '../profile/options'
import PageSkeleton from '../components/PageSkeleton'

const EMPTY: JobInput = {
  title: '',
  service: 'nounou',
  availability: 'temps_plein',
  budget: '',
  location: '',
  description: '',
}

/** Publication (/mes-annonces/nouvelle) ou modification (/mes-annonces/:id) d'une annonce. */
export default function JobFormPage() {
  const { t } = useI18n()
  const id = useParams().id
  const [initial, setInitial] = useState<JobInput | null | undefined>(id ? undefined : EMPTY)

  useEffect(() => {
    if (!id) return
    getJob<MyJob>(Number(id)).then(
      (job) =>
        setInitial({
          title: job.title,
          service: job.service.slug,
          availability: job.availability,
          budget: job.budget === null ? '' : String(Number(job.budget)),
          location: job.location,
          description: job.description,
        }),
      () => setInitial(null),
    )
  }, [id])

  if (initial === undefined) return <PageSkeleton />
  if (initial === null) return <p className="error">{t('jobs.notFound')}</p>
  return <JobForm id={id ? Number(id) : null} initial={initial} />
}

function JobForm({ id, initial }: { id: number | null; initial: JobInput }) {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const [form, setForm] = useState<JobInput>(initial)
  const [error, setError] = useState('')
  const [noProfile, setNoProfile] = useState(false)
  const [busy, setBusy] = useState(false)

  const update = <K extends keyof JobInput>(key: K, value: JobInput[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    const data: JobInput = {
      ...form,
      title: form.title.trim(),
      location: form.location.trim(),
      description: form.description.trim(),
      budget: form.budget === '' ? null : form.budget,
    }
    try {
      if (id) await updateJob(id, data)
      else await createJob(data)
      navigate('/mes-annonces')
    } catch (err) {
      // Sans profil client, l'API répond 400 {"detail": …} (et non des erreurs par champ)
      const missingProfile =
        !id &&
        err instanceof ApiError &&
        err.status === 400 &&
        typeof err.data === 'object' &&
        err.data !== null &&
        'detail' in err.data
      setNoProfile(missingProfile)
      setError(missingProfile ? t('jobForm.noProfile') : errorText(err, lang, t, 'jobForm.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>{id ? t('jobForm.edit') : t('jobForm.create')}</h1>
      <Field label={t('jobForm.title')}>
        <input
          type="text"
          required
          maxLength={120}
          placeholder={t('jobForm.title.placeholder')}
          value={form.title}
          onChange={(e) => update('title', e.target.value)}
        />
      </Field>

      <fieldset className="choices">
        <legend className="field-label">{t('jobForm.service')}</legend>
        {SERVICES.map((slug) => (
          <label key={slug} className={`chip ${form.service === slug ? 'selected' : ''}`}>
            <input
              type="radio"
              name="service"
              checked={form.service === slug}
              onChange={() => update('service', slug as ServiceSlug)}
            />
            {t(`service.${slug}`)}
          </label>
        ))}
      </fieldset>

      <fieldset className="choices">
        <legend className="field-label">{t('jobForm.availability')}</legend>
        {AVAILABILITIES.map((value) => (
          <label key={value} className={`chip ${form.availability === value ? 'selected' : ''}`}>
            <input
              type="radio"
              name="availability"
              checked={form.availability === value}
              onChange={() => update('availability', value as Availability)}
            />
            {t(`availability.${value}`)}
          </label>
        ))}
      </fieldset>

      <Field label={t('jobForm.budget')} hint={t('profile.amount.hint')}>
        <input
          type="number"
          inputMode="decimal"
          min={0}
          step="any"
          value={form.budget ?? ''}
          onChange={(e) => update('budget', e.target.value)}
        />
      </Field>
      <Field label={t('jobForm.location')} hint={t('jobForm.location.hint')}>
        <input type="text" value={form.location} onChange={(e) => update('location', e.target.value)} />
      </Field>
      <Field label={t('jobForm.description')}>
        <textarea
          rows={4}
          placeholder={t('jobForm.description.placeholder')}
          value={form.description}
          onChange={(e) => update('description', e.target.value)}
        />
      </Field>

      {error && <p className="error" role="alert">{error}</p>}
      {noProfile && (
        <Link to="/profil" className="button secondary">
          {t('home.profile.create')}
        </Link>
      )}
      <button type="submit" className="button primary" disabled={busy}>
        {busy ? t('common.loading') : id ? t('jobForm.submit.edit') : t('jobForm.submit.create')}
      </button>
      <Link to="/mes-annonces" className="link">
        {t('profile.cancel')}
      </Link>
    </form>
  )
}
