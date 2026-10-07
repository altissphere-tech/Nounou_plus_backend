import { afterEach, describe, expect, it } from 'vitest'
import {
  IDLE_LIMIT_MS,
  IDLE_WARNING_MS,
  consumeIdleLogout,
  idleState,
  markActivity,
  rememberIdleLogout,
  sessionExpiredByIdle,
} from './idle'

afterEach(() => {
  localStorage.clear()
  sessionStorage.clear()
})

describe('déconnexion après inactivité', () => {
  const start = 1_000_000

  it('active, puis avertissement 1 min avant, puis expirée à 30 min', () => {
    expect(IDLE_LIMIT_MS).toBe(30 * 60 * 1000)
    expect(idleState(start, start + 10 * 60 * 1000)).toBe('active')
    expect(idleState(start, start + IDLE_LIMIT_MS - IDLE_WARNING_MS)).toBe('warning')
    expect(idleState(start, start + IDLE_LIMIT_MS)).toBe('expired')
  })

  it("application rouverte après 30 min d'inactivité : session fermée", () => {
    markActivity(start)
    expect(sessionExpiredByIdle(start + 5 * 60 * 1000)).toBe(false)
    expect(sessionExpiredByIdle(start + IDLE_LIMIT_MS + 1)).toBe(true)
  })

  it('le message « déconnecté pour inactivité » ne s’affiche qu’une fois', () => {
    rememberIdleLogout()
    expect(consumeIdleLogout()).toBe(true)
    expect(consumeIdleLogout()).toBe(false)
  })
})
