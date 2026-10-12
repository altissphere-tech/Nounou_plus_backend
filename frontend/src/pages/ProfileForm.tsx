import { useState } from 'react'
import { HelpCard, MyProfilePreviewCard } from '../components/SideCards'
import WithAside from '../components/WithAside'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { saveClientProfile, saveWorkerProfile } from '../api/profiles'
import type { Availability, ServiceSlug } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import PhotoPicker from '../components/PhotoPicker'
import { useI18n } from '../i18n/I18nContext'
import { AVAILABILITIES, SERVICES } from '../profile/options'
import type { MyProfile } from '../profile/useMyProfile'
import { useMyProfile } from '../profile/useMyProfile'
import PageSkeleton from '../components/PageSkeleton'

interface FormState {
  firstName: string
  lastName: string
  location: string
  services: ServiceSlug[]
  availability: Availability
  amount: string // salaire souhaité (travailleur) ou budget (client)
  experience: string
  text: string // présentation (travailleur) ou besoins (client)
}

const EMPTY: FormState = {
  firstName: '',
  lastName: '',
  location: '',
  services: [],
  availability: 'temps_plein',
  amount: '',
  experience: '0',
  text: '',
}

/** Valeurs de départ du formulaire : vides, ou celles du profil existant. */
function initialForm(data: MyProfile): FormState {
  if (!data.profile) return EMPTY
  if (data.kind === 'worker') {
    const p = data.profile
    return {
      firstName: p.first_name,
      lastName: p.last_name,
      location: p.location,
      services: p.services_list,
      availability: p.availability,
      amount: String(Number(p.expected_salary)),
      experience: String(p.years_experience),
      text: p.bio,
    }
  }
  const p = data.profile
  return {
    ...EMPTY,
    firstName: p.first_name,
    lastName: p.last_name,
    location: p.location,
    services: p.services_list,
    availability: p.availability_needed,
    amount: p.budget === null ? '' : String(Number(p.budget)),
    text: p.needs_description,
  }
}

/** Création ou modification du profil, selon le rôle (famille ou travailleur). */
export default function ProfilePage() {
  const { t } = useI18n()
  const { user } = useAuth()
  const { data, failed } = useMyProfile(user!.role)
  if (failed) return <p className="error">{t('profile.loadError')}</p>
  if (!data) return <PageSkeleton />
  return <ProfileForm data={data} />
}

function ProfileForm({ data }: { data: MyProfile }) {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const isWorker = data.kind === 'worker'
  const exists = Boolean(data.profile)

  const [form, setForm] = useState<FormState>(() => initialForm(data))
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  function toggleService(slug: ServiceSlug) {
    setError('')
    update(
      'services',
      form.services.includes(slug) ? form.services.filter((s) => s !== slug) : [...form.services, slug],
    )
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (form.services.length === 0) {
      setError(t('profile.error.services'))
      return
    }
    setBusy(true)
    try {
      const common = {
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        location: form.location.trim(),
      }
      if (isWorker) {
        await saveWorkerProfile(
          {
            ...common,
            bio: form.text.trim(),
            services: form.services.join(','),
            years_experience: Number(form.experience) || 0,
            availability: form.availability,
            expected_salary: form.amount,
          },
          exists,
        )
      } else {
        await saveClientProfile(
          {
            ...common,
            needs_description: form.text.trim(),
            services_needed: form.services.join(','),
            availability_needed: form.availability,
            budget: form.amount === '' ? null : form.amount,
          },
          exists,
        )
      }
      navigate('/accueil', { state: { saved: true } })
    } catch (err) {
      setError(errorText(err, lang, t, 'profile.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack">
      <WithAside
        aside={
          <>
            <MyProfilePreviewCard />
            <HelpCard />
          </>
        }
      >
        <PhotoPicker name={`${form.firstName} ${form.lastName}`.trim() || '?'} />
        <form className="card" onSubmit={submit}>
          <h1>{exists ? t('profile.edit.title') : t('profile.create.title')}</h1>
          {!exists && (
            <p className="muted">
              {isWorker ? t('profile.create.intro.worker') : t('profile.create.intro.client')}
            </p>
          )}

          <Field label={t('profile.firstName')}>
            <input
              type="text"
              required
              autoComplete="given-name"
              value={form.firstName}
              onChange={(e) => update('firstName', e.target.value)}
            />
          </Field>
          <Field label={t('profile.lastName')} hint={t('profile.lastName.hint')}>
            <input
              type="text"
              required
              autoComplete="family-name"
              value={form.lastName}
              onChange={(e) => update('lastName', e.target.value)}
            />
          </Field>
          <Field label={t('profile.location')}>
            <input
              type="text"
              required
              placeholder={t('profile.location.placeholder')}
              value={form.location}
              onChange={(e) => update('location', e.target.value)}
            />
          </Field>

          <fieldset className="choices">
            <legend className="field-label">
              {isWorker ? t('profile.services.worker') : t('profile.services.client')}
            </legend>
            {SERVICES.map((slug) => (
              <label key={slug} className={`chip ${form.services.includes(slug) ? 'selected' : ''}`}>
                <input
                  type="checkbox"
                  checked={form.services.includes(slug)}
                  onChange={() => toggleService(slug)}
                />
                {t(`service.${slug}`)}
              </label>
            ))}
            <span className="field-hint">{t('profile.services.hint')}</span>
          </fieldset>

          <fieldset className="choices">
            <legend className="field-label">
              {isWorker ? t('profile.availability.worker') : t('profile.availability.client')}
            </legend>
            {AVAILABILITIES.map((value) => (
              <label key={value} className={`chip ${form.availability === value ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="availability"
                  checked={form.availability === value}
                  onChange={() => update('availability', value)}
                />
                {t(`availability.${value}`)}
              </label>
            ))}
          </fieldset>

          {isWorker && (
            <Field label={t('profile.experience')}>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                max={50}
                required
                value={form.experience}
                onChange={(e) => update('experience', e.target.value)}
              />
            </Field>
          )}

          <Field label={isWorker ? t('profile.salary') : t('profile.budget')} hint={t('profile.amount.hint')}>
            <input
              type="number"
              inputMode="decimal"
              min={0}
              step="any"
              required={isWorker}
              value={form.amount}
              onChange={(e) => update('amount', e.target.value)}
            />
          </Field>

          <Field label={isWorker ? t('profile.bio') : t('profile.needs')}>
            <textarea
              rows={4}
              placeholder={isWorker ? t('profile.bio.placeholder') : t('profile.needs.placeholder')}
              value={form.text}
              onChange={(e) => update('text', e.target.value)}
            />
          </Field>

          {error && <p className="error" role="alert">{error}</p>}
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? t('common.loading') : t('profile.save')}
          </button>
          <Link to="/accueil" className="link">
            {t('profile.cancel')}
          </Link>
        </form>
      </WithAside>
    </section>
  )
}
