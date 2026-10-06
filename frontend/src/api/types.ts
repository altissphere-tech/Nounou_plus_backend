// Formats renvoyés par l'API (voir la documentation interactive : /api/docs/).

export type Role = 'client' | 'travailleur' | 'admin'

export interface User {
  id: number
  phone: string
  role: Role
  phone_verified: boolean
  created_at: string
}

export interface Me extends User {
  warnings: { message: string; date: string }[]
}

export interface LoginResponse {
  message: string
  tokens: { access: string; refresh: string }
  user: User
}
