/**
 * Déconnexion après inactivité (choix du fondateur) : 30 minutes sans geste de la
 * personne (toucher, clavier, défilement), avec un avertissement 1 minute avant.
 * Les actualisations automatiques (messages, notifications) ne comptent pas.
 *
 * La date de la dernière activité est gardée dans le navigateur : elle vaut pour
 * tous les onglets, et l'application la vérifie aussi en se rouvrant. Le serveur
 * applique la même règle (SESSION_IDLE_MINUTES = 30 côté Django).
 */
export const IDLE_LIMIT_MS = 30 * 60 * 1000
export const IDLE_WARNING_MS = 60 * 1000

const LAST_ACTIVITY_KEY = 'nounou.lastActivity'
const IDLE_LOGOUT_KEY = 'nounou.idleLogout'

export type IdleState = 'active' | 'warning' | 'expired'

/** Où en est la session, d'après la dernière activité. */
export function idleState(lastActivity: number, now: number): IdleState {
  const idle = now - lastActivity
  if (idle >= IDLE_LIMIT_MS) return 'expired'
  if (idle >= IDLE_LIMIT_MS - IDLE_WARNING_MS) return 'warning'
  return 'active'
}

export function markActivity(now = Date.now()): void {
  try {
    localStorage.setItem(LAST_ACTIVITY_KEY, String(now))
  } catch {
    // stockage indisponible : la règle reste appliquée par le serveur
  }
}

/** Dernière activité connue (null si jamais enregistrée). */
export function lastActivity(): number | null {
  try {
    const value = Number(localStorage.getItem(LAST_ACTIVITY_KEY))
    return value > 0 ? value : null
  } catch {
    return null
  }
}

/** true si la session doit être fermée pour inactivité (ex : application rouverte le lendemain). */
export function sessionExpiredByIdle(now = Date.now()): boolean {
  const last = lastActivity()
  return last !== null && idleState(last, now) === 'expired'
}

/** Mémorise la raison de la déconnexion, pour l'expliquer sur l'écran suivant. */
export function rememberIdleLogout(): void {
  try {
    sessionStorage.setItem(IDLE_LOGOUT_KEY, '1')
  } catch {
    // sans importance
  }
}

/** Lit (une seule fois) si la dernière déconnexion venait de l'inactivité. */
export function consumeIdleLogout(): boolean {
  try {
    const value = sessionStorage.getItem(IDLE_LOGOUT_KEY) === '1'
    sessionStorage.removeItem(IDLE_LOGOUT_KEY)
    return value
  } catch {
    return false
  }
}
