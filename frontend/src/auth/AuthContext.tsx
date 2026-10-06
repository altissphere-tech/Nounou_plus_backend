import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { getMe, verifyCode } from '../api/accounts'
import { loadTokens, saveTokens, setSessionExpiredHandler } from '../api/client'
import type { Me } from '../api/types'

interface AuthValue {
  /** L'utilisateur connecté, null s'il n'est pas connecté, undefined pendant le chargement. */
  user: Me | null | undefined
  login: (phone: string, code: string) => Promise<void>
  logout: () => void
  reload: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Sans token enregistré, on sait tout de suite que personne n'est connecté
  const [user, setUser] = useState<Me | null | undefined>(() => (loadTokens() ? undefined : null))

  const logout = useCallback(() => {
    saveTokens(null)
    setUser(null)
  }, [])

  const reload = useCallback(async () => {
    if (!loadTokens()) {
      setUser(null)
      return
    }
    try {
      setUser(await getMe())
    } catch {
      setUser(null)
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
      getMe().then(setUser, () => setUser(null))
    }
  }, [])

  const value = useMemo(() => ({ user, login, logout, reload }), [user, login, logout, reload])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth doit être utilisé dans <AuthProvider>')
  return value
}
