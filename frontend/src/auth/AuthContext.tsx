import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { getMe, verifyCode } from '../api/accounts'
import { ApiError, loadTokens, saveTokens, setSessionExpiredHandler } from '../api/client'
import type { Me } from '../api/types'

interface AuthValue {
  /** L'utilisateur connecté, null s'il n'est pas connecté, undefined pendant le chargement. */
  user: Me | null | undefined
  /**
   * true si une session existe mais que le serveur est injoignable (pas d'internet) :
   * on ne déconnecte pas l'utilisateur, on lui propose de réessayer.
   */
  unreachable: boolean
  login: (phone: string, code: string) => Promise<void>
  logout: () => void
  reload: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Sans token enregistré, on sait tout de suite que personne n'est connecté
  const [user, setUser] = useState<Me | null | undefined>(() => (loadTokens() ? undefined : null))
  const [unreachable, setUnreachable] = useState(false)

  const logout = useCallback(() => {
    saveTokens(null)
    setUnreachable(false)
    setUser(null)
  }, [])

  const reload = useCallback(async () => {
    if (!loadTokens()) {
      setUser(null)
      return
    }
    try {
      setUser(await getMe())
      setUnreachable(false)
    } catch (error) {
      if (error instanceof ApiError) {
        setUser(null) // session refusée par le serveur
      } else {
        setUnreachable(true) // pas de réponse : problème de connexion, la session est gardée
      }
    }
  }, [])

  const login = useCallback(
    async (phone: string, code: string) => {
      const response = await verifyCode(phone, code)
      saveTokens(response.tokens)
      await reload()
    },
    [reload],
  )

  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    // Session enregistrée : on récupère le compte auprès du serveur
    if (loadTokens()) {
      getMe().then(
        (me) => setUser(me),
        (error) => (error instanceof ApiError ? setUser(null) : setUnreachable(true)),
      )
    }
    // Retour de la connexion : on réessaie automatiquement
    const onOnline = () => {
      if (loadTokens()) void reload()
    }
    window.addEventListener('online', onOnline)
    return () => window.removeEventListener('online', onOnline)
  }, [reload])

  const value = useMemo(
    () => ({ user, unreachable, login, logout, reload }),
    [user, unreachable, login, logout, reload],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth doit être utilisé dans <AuthProvider>')
  return value
}
