import { api } from './client'
import type { LoginResponse, Me } from './types'

// Endpoints de la rubrique « Comptes » de l'API.

export function register(phone: string, role: 'client' | 'travailleur') {
  return api<{ message: string }>('POST', '/api/accounts/register/', { phone, role })
}

export function requestCode(phone: string) {
  return api<{ message: string }>('POST', '/api/accounts/otp/request/', { phone })
}

export function verifyCode(phone: string, code: string) {
  return api<LoginResponse>('POST', '/api/accounts/otp/verify/', { phone, code })
}

export function getMe() {
  return api<Me>('GET', '/api/accounts/me/')
}
