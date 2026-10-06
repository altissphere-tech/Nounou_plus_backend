import { Heart } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import { toggleFavorite, useFavoriteIds } from '../lists/favorites'

/** Cœur « favori » sur une carte ou une fiche (travailleur pour une famille, annonce pour un travailleur). */
export default function FavoriteButton({
  kind,
  id,
  name,
  onDark = false,
}: {
  kind: 'workers' | 'jobs'
  id: number
  name: string
  onDark?: boolean
}) {
  const { t } = useI18n()
  const { user } = useAuth()
  const on = useFavoriteIds(kind, user?.id)?.has(id) ?? false
  return (
    <button
      type="button"
      className={`favorite ${on ? 'on' : ''} ${onDark ? 'on-dark' : ''}`}
      aria-pressed={on}
      aria-label={t(on ? 'favorite.remove' : 'favorite.add', { name })}
      onClick={() => toggleFavorite(kind, id).catch(() => window.alert(t('favorite.error')))}
    >
      <Heart size={20} fill={on ? 'currentColor' : 'none'} />
    </button>
  )
}
