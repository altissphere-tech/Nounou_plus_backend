import { useRef, useState } from 'react'
import { Camera, Trash2 } from 'lucide-react'
import { deletePhoto, uploadPhoto } from '../api/accounts'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { useMyPhoto } from '../profile/useMyPhoto'
import Avatar from './Avatar'
import { errorText } from './errors'

/**
 * Photo de profil : envoyer, remplacer, supprimer. Elle est visible par les autres
 * (même avant un match) seulement après validation par l'équipe NOUNOU+.
 */
export default function PhotoPicker({ name }: { name: string }) {
  const { t, lang } = useI18n()
  const { user, reload } = useAuth()
  const [version, setVersion] = useState(0)
  const photo = useMyPhoto(user?.photo_status, version)
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function choose(file: File | undefined) {
    if (!file) return
    setError('')
    setBusy(true)
    try {
      await uploadPhoto(file)
      await reload()
      setVersion((v) => v + 1)
    } catch (err) {
      setError(errorText(err, lang, t, 'photo.error'))
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  async function remove() {
    if (!window.confirm(t('photo.deleteConfirm'))) return
    setBusy(true)
    try {
      await deletePhoto()
      await reload()
    } finally {
      setBusy(false)
    }
  }

  const status = user?.photo_status ?? 'aucune'
  return (
    <div className="card photo-picker">
      <h2 className="overline">{t('photo.title')}</h2>
      <div className="person">
        <Avatar name={name} src={photo} size={72} />
        <div className="person-text">
          {status === 'aucune' && <span>{t('photo.none')}</span>}
          {status === 'en_attente' && <span className="badge">{t('photo.pending')}</span>}
          {status === 'validee' && <span className="verified">✔ {t('photo.approved')}</span>}
          {status === 'rejetee' && (
            <span className="error-text">
              {t('photo.rejected')} {user?.photo_rejection_reason}
            </span>
          )}
          <span className="muted">{t('photo.rule')}</span>
        </div>
      </div>
      <input
        ref={input}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="visually-hidden"
        aria-label={t('photo.choose')}
        onChange={(e) => choose(e.target.files?.[0])}
      />
      <div className="actions">
        <button type="button" className="button small primary" disabled={busy} onClick={() => input.current?.click()}>
          <Camera size={16} aria-hidden="true" /> {busy ? t('common.loading') : status === 'aucune' || status === 'rejetee' ? t('photo.choose') : t('photo.change')}
        </button>
        {(status === 'en_attente' || status === 'validee') && (
          <button type="button" className="button small secondary" disabled={busy} onClick={remove}>
            <Trash2 size={16} aria-hidden="true" /> {t('photo.delete')}
          </button>
        )}
      </div>
      {error && <p className="error" role="alert">{error}</p>}
    </div>
  )
}
