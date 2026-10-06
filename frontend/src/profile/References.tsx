import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Trash2 } from 'lucide-react'
import { addReference, myReferences, removeReference } from '../api/trust'
import type { WorkerReference } from '../api/types'
import { errorText } from '../components/errors'
import Field from '../components/Field'
import { useI18n } from '../i18n/I18nContext'

const MAX_REFERENCES = 3

/**
 * Références du travailleur (ancien employeur, voisin…). L'équipe NOUNOU+ les appelle ;
 * leurs coordonnées ne sont jamais montrées aux familles.
 */
export default function References() {
  const { t, lang } = useI18n()
  const [items, setItems] = useState<WorkerReference[] | null>(null)
  const [version, setVersion] = useState(0)
  const [form, setForm] = useState({ name: '', phone: '', relationship: '' })
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    myReferences().then(setItems, () => setItems([]))
  }, [version])

  const active = items?.filter((r) => r.status !== 'non_confirmee').length ?? 0
  const set = (field: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [field]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault()
    setMessage(null)
    setBusy(true)
    try {
      await addReference(form)
      setForm({ name: '', phone: '', relationship: '' })
      setMessage({ ok: true, text: t('refs.added') })
      setVersion((v) => v + 1)
    } catch (err) {
      setMessage({ ok: false, text: errorText(err, lang, t, 'refs.error') })
    } finally {
      setBusy(false)
    }
  }

  async function remove(reference: WorkerReference) {
    if (!window.confirm(t('refs.removeConfirm', { name: reference.name }))) return
    await removeReference(reference.id)
    setVersion((v) => v + 1)
  }

  return (
    <div className="card">
      <h2>{t('refs.title')}</h2>
      <p className="muted">{t('refs.intro')}</p>
      {items?.map((reference) => (
        <div key={reference.id} className="doc-row">
          <div>
            <strong>{reference.name}</strong>
            <span className="muted">
              {' '}
              · {reference.relationship} · {reference.phone}
            </span>
          </div>
          <span className="actions">
            <span className={`status ref-${reference.status}`}>{t(`refStatus.${reference.status}`)}</span>
            <button
              type="button"
              className="icon-button light"
              aria-label={t('refs.remove', { name: reference.name })}
              onClick={() => remove(reference)}
            >
              <Trash2 size={16} />
            </button>
          </span>
        </div>
      ))}
      {active < MAX_REFERENCES ? (
        <form className="stack" onSubmit={submit}>
          <Field label={t('refs.name')}>
            <input required maxLength={150} value={form.name} onChange={(e) => set('name')(e.target.value)} />
          </Field>
          <Field label={t('refs.phone')} hint={t('phone.hint')}>
            <input
              type="tel"
              inputMode="tel"
              required
              placeholder={t('phone.placeholder')}
              value={form.phone}
              onChange={(e) => set('phone')(e.target.value)}
            />
          </Field>
          <Field label={t('refs.relationship')} hint={t('refs.relationship.hint')}>
            <input
              required
              maxLength={150}
              value={form.relationship}
              onChange={(e) => set('relationship')(e.target.value)}
            />
          </Field>
          {message && <p className={message.ok ? 'info-banner' : 'error'} role="status">{message.text}</p>}
          <button type="submit" className="button secondary" disabled={busy}>
            {busy ? t('common.loading') : t('refs.add')}
          </button>
        </form>
      ) : (
        <p className="muted small-text">{t('refs.max')}</p>
      )}
    </div>
  )
}
