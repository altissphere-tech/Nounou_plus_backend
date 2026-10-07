import { api } from './client'
import type { AuthOptions, LoginResponse, Me, SocialProvider, User } from './types'

// Endpoints de la rubrique « Comptes » de l'API.

type Role = 'client' | 'travailleur'

/** Inscription par téléphone : un code SMS est envoyé ensuite. */
export function register(phone: string, role: Role) {
  return api<{ message: string }>('POST', '/api/accounts/register/', { phone, role })
}

/** Inscription avec e-mail + mot de passe : la personne est connectée tout de suite. */
export function registerWithEmail(data: { phone: string; role: Role; email: string; password: string }) {
  return api<LoginResponse>('POST', '/api/accounts/register/', data)
}

export function requestCode(phone: string) {
  return api<{ message: string }>('POST', '/api/accounts/otp/request/', { phone })
}

export function verifyCode(phone: string, code: string) {
  return api<LoginResponse>('POST', '/api/accounts/otp/verify/', { phone, code })
}

export function loginWithEmail(email: string, password: string) {
  return api<LoginResponse>('POST', '/api/accounts/login/', { email, password })
}

export const getAuthOptions = () => api<AuthOptions>('GET', '/api/accounts/auth-options/')

/**
 * Connexion Google / Apple. Pour un nouveau compte, la première réponse est une
 * erreur 400 avec `registration_required` : on redemande alors avec le rôle et le numéro.
 */
export function socialLogin(provider: SocialProvider, idToken: string, extra: { role?: Role; phone?: string } = {}) {
  return api<LoginResponse>('POST', '/api/accounts/social/', { provider, id_token: idToken, ...extra })
}

export const forgotPassword = (email: string) =>
  api<{ message: string }>('POST', '/api/accounts/password/forgot/', { email })

export const resetPassword = (uid: string, token: string, password: string) =>
  api<{ message: string }>('POST', '/api/accounts/password/reset/', { uid, token, password })

export const changePassword = (newPassword: string, currentPassword?: string) =>
  api<{ message: string }>('POST', '/api/accounts/password/change/', {
    new_password: newPassword,
    ...(currentPassword ? { current_password: currentPassword } : {}),
  })

export const changeEmail = (email: string, currentPassword?: string) =>
  api<{ message: string; user: User }>('POST', '/api/accounts/email/', {
    email,
    ...(currentPassword ? { current_password: currentPassword } : {}),
  })

export function getMe() {
  return api<Me>('GET', '/api/accounts/me/')
}

// --- Photo de profil ---------------------------------------------------------

export function uploadPhoto(file: File) {
  const form = new FormData()
  form.append('photo', file)
  return api<{ message: string; user: User }>('POST', '/api/accounts/photo/', form)
}

export const deletePhoto = () => api<{ message: string }>('DELETE', '/api/accounts/photo/')
