import { useState } from 'react'
import type { FormEvent } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { sendReport } from '../api/trust'
import type { ReportCategory } from '../api/types'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import { useI18n } from '../i18n/I18nContext'

const CATEGORIES: ReportCategory[] = ['faux_profil', 'comportement_inapproprie', 'arnaque', 'securite', 'autre']

/** Signalement anonyme d'un profil (travailleur pour une famille, famille pour un travailleur). */
export default function ReportForm() {
  const { t, lang } = useI18n()
  const navigate = useNavigate()
  const profileId = Number(useParams().profileId)
  const name = (useLocation().state as { name?: string } | null)?.name ?? t('report.someone')
  const [category, setCategory] = useState<ReportCategory | null>(null)
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!category) return
    if (category === 'autre' && !description.trim()) {
      setError(t('report.descriptionRequired'))
      return
    }
    setBusy(true)
    setError('')
    try {
      await sendReport(profileId, category, description.trim())
      setSent(true)
    } catch (err) {
      // Signalement déjà en cours : l'API répond 400 {"detail": …}
      const duplicate =
        err instanceof ApiError && err.status === 400 && typeof err.data === 'object' && err.data !== null && 'detail' in err.data
      setError(duplicate ? t('report.duplicate') : errorText(err, lang, t, 'report.error'))
    } finally {
      setBusy(false)
    }
  }

  if (sent) {
    return (
      <div className="card">
        <p className="info-banner" role="status">
          ✔ {t('report.sent')}
        </p>
        <p className="muted">{t('report.anonymous')}</p>
        <button type="button" className="button secondary" onClick={() => navigate(-1)}>
          {t('common.back')}
        </button>
      </div>
    )
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>{t('report.title')}</h1>
      <p className="profile-name">{t('report.about', { name })}</p>
      <p className="notice">🔒 {t('report.anonymous')}</p>
      <fieldset className="choices vertical">
        <legend className="field-label">{t('report.category')}</legend>
        {CATEGORIES.map((value) => (
          <label key={value} className={`chip ${category === value ? 'selected' : ''}`}>
            <input
              type="radio"
              name="category"
              required
              checked={category === value}
              onChange={() => {
                setError('')
                setCategory(value)
              }}
            />
            {t(`reportCategory.${value}`)}
          </label>
        ))}
      </fieldset>
      <Field label={category === 'autre' ? t('report.description') : t('report.description.optional')}>
        <textarea
          rows={4}
          maxLength={2000}
          placeholder={t('report.description.placeholder')}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </Field>
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" className="button danger" disabled={busy || !category}>
        {busy ? t('common.loading') : t('report.send')}
      </button>
      <button type="button" className="link" onClick={() => navigate(-1)}>
        {t('profile.cancel')}
      </button>
    </form>
  )
}
