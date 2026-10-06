import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import { myDocuments, uploadDocument } from '../api/trust'
import type { DocType, VerificationDocument } from '../api/types'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import { useI18n } from '../i18n/I18nContext'

const MAX_SIZE = 5 * 1024 * 1024 // 5 Mo, comme sur le serveur
const DOC_TYPES: DocType[] = ['identite', 'reference']

/** Envoi des documents de vérification et suivi de leur statut (travailleurs). */
export default function Documents() {
  const { t, lang } = useI18n()
  const [data, setData] = useState<{ is_verified: boolean; documents: VerificationDocument[] } | null | undefined>(
    undefined,
  )
  const [version, setVersion] = useState(0)
  const [docType, setDocType] = useState<DocType>('identite')
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    myDocuments().then(setData, (err) => setData(err instanceof ApiError && err.status === 404 ? null : undefined))
  }, [version])

  if (data === undefined) return <p className="muted">{t('common.loading')}</p>
  if (data === null) {
    return (
      <div className="card">
        <p>{t('docs.noProfile')}</p>
        <Link to="/profil" className="button primary">
          {t('home.profile.create')}
        </Link>
      </div>
    )
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!file) return
    setMessage(null)
    if (file.size > MAX_SIZE) {
      setMessage({ ok: false, text: t('docs.tooBig') })
      return
    }
    setBusy(true)
    try {
      await uploadDocument(docType, file)
      setMessage({ ok: true, text: t('docs.sent') })
      setFile(null)
      ;(event.target as HTMLFormElement).reset()
      setVersion((v) => v + 1)
    } catch (err) {
      setMessage({ ok: false, text: errorText(err, lang, t, 'docs.error') })
    } finally {
      setBusy(false)
    }
  }

  const date = (iso: string) => new Date(iso).toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB')

  return (
    <section className="stack">
      <h1>{t('docs.title')}</h1>
      <div className={`notice ${data.is_verified ? 'success' : ''}`}>
        <strong>{data.is_verified ? `✔ ${t('docs.verified')}` : t('docs.notVerified')}</strong>
        <span>{t('docs.intro')}</span>
      </div>

      <form className="card" onSubmit={submit}>
        <fieldset className="choices">
          <legend className="field-label">{t('docs.type')}</legend>
          {DOC_TYPES.map((type) => (
            <label key={type} className={`chip ${docType === type ? 'selected' : ''}`}>
              <input type="radio" name="doc_type" checked={docType === type} onChange={() => setDocType(type)} />
              {t(`docType.${type}`)}
            </label>
          ))}
        </fieldset>
        <Field label={t('docs.file')} hint={t('docs.file.hint')}>
          <input
            type="file"
            required
            accept="image/jpeg,image/png,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </Field>
        {message && <p className={message.ok ? 'info-banner' : 'error'} role="status">{message.text}</p>}
        <button type="submit" className="button primary" disabled={busy || !file}>
          {busy ? t('common.loading') : t('docs.send')}
        </button>
      </form>

      <div className="card">
        <h2>{t('docs.list')}</h2>
        {data.documents.length === 0 && <p className="muted">{t('docs.none')}</p>}
        {data.documents.map((doc) => (
          <div key={doc.id} className="doc-row">
            <div>
              <strong>{t(`docName.${doc.doc_type}`)}</strong>
              <span className="muted"> · {date(doc.created_at)}</span>
              {doc.status === 'rejete' && doc.rejection_reason && (
                <p className="error-text">{t('docs.reason', { reason: doc.rejection_reason })}</p>
              )}
            </div>
            <span className={`status doc-${doc.status}`}>{t(`docStatus.${doc.status}`)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
