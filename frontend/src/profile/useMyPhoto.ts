import { useEffect, useState } from 'react'
import { apiBlobUrl } from '../api/client'
import type { PhotoStatus } from '../api/types'

/**
 * Sa propre photo (même en attente de validation), chargée avec la session.
 * `version` permet de la recharger après un envoi.
 */
export function useMyPhoto(status: PhotoStatus | undefined, version = 0): string | null {
  const [url, setUrl] = useState<string | null>(null)
  const hasPhoto = status === 'en_attente' || status === 'validee'
  useEffect(() => {
    if (!hasPhoto) return
    let current: string | null = null
    let cancelled = false
    apiBlobUrl('/api/accounts/photo/').then(
      (blobUrl) => {
        current = blobUrl
        if (cancelled) URL.revokeObjectURL(blobUrl)
        else setUrl(blobUrl)
      },
      () => !cancelled && setUrl(null),
    )
    return () => {
      cancelled = true
      if (current) URL.revokeObjectURL(current)
    }
  }, [hasPhoto, version])
  return hasPhoto ? url : null
}
