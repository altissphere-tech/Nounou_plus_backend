import { describe, expect, it } from 'vitest'
import { rememberCredentials, takeCredentials } from './pendingSignup'

describe('identifiants en attente du code SMS', () => {
  it('sont rendus une seule fois, pour le bon numéro', () => {
    rememberCredentials({ phone: '+243812300001', email: 'marie@example.com', password: 'Secret42!' })
    expect(takeCredentials('+243812300001')?.email).toBe('marie@example.com')
    expect(takeCredentials('+243812300001')).toBeNull()
  })

  it("ne servent pas pour un autre numéro (et sont oubliés)", () => {
    rememberCredentials({ phone: '+243812300001', email: 'marie@example.com', password: 'Secret42!' })
    expect(takeCredentials('+243899999999')).toBeNull()
    expect(takeCredentials('+243812300001')).toBeNull()
  })
})
