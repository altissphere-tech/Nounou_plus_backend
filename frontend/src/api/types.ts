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

export type ServiceSlug = 'nounou' | 'menage' | 'cuisine'
export type Availability = 'temps_plein' | 'temps_partiel' | 'weekends'

export interface Rating {
  average: string | null
  count: number
}

export interface WorkerProfile {
  id: number
  first_name: string
  last_name: string
  bio: string
  services_list: ServiceSlug[]
  years_experience: number
  availability: Availability
  expected_salary: string
  location: string
  is_verified: boolean
  rating: Rating
  phone_display: string
}

export interface ClientProfile {
  id: number
  first_name: string
  last_name: string
  location: string
  services_list: ServiceSlug[]
  availability_needed: Availability
  budget: string | null
  needs_description: string
  rating: Rating
}

/** Données envoyées pour créer / modifier un profil travailleur. */
export interface WorkerProfileInput {
  first_name: string
  last_name: string
  bio: string
  services: string // ex : "nounou,cuisine"
  years_experience: number
  availability: Availability
  expected_salary: string
  location: string
}

/** Données envoyées pour créer / modifier un profil client. */
export interface ClientProfileInput {
  first_name: string
  last_name: string
  location: string
  services_needed: string // ex : "nounou,menage"
  availability_needed: Availability
  budget: string | null
  needs_description: string
}
