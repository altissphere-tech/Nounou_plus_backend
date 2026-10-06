import { useEffect, useState } from 'react'
import { getMyClientProfile, getMyWorkerProfile } from '../api/profiles'
import type { ClientProfile, Role, WorkerProfile } from '../api/types'

export type MyProfile =
  | { kind: 'worker'; profile: WorkerProfile | null }
  | { kind: 'client'; profile: ClientProfile | null }

interface State {
  data: MyProfile | undefined // undefined = chargement en cours
  failed: boolean
}

/** Charge le profil (travailleur ou client) de l'utilisateur connecté. */
export function useMyProfile(role: Role): State {
  const [state, setState] = useState<State>({ data: undefined, failed: false })

  useEffect(() => {
    let cancelled = false
    const request: Promise<MyProfile> =
      role === 'travailleur'
        ? getMyWorkerProfile().then((profile) => ({ kind: 'worker' as const, profile }))
        : getMyClientProfile().then((profile) => ({ kind: 'client' as const, profile }))
    request.then(
      (data) => !cancelled && setState({ data, failed: false }),
      () => !cancelled && setState({ data: undefined, failed: true }),
    )
    return () => {
      cancelled = true
    }
  }, [role])

  return state
}
