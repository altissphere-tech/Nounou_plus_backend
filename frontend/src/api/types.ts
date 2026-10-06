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

/** Réponse paginée de l'API (pages de 20). */
export interface Page<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** Profil travailleur tel que le voient les autres (nom réduit à l'initiale). */
export type PublicWorker = WorkerProfile

export type JobStatus = 'ouverte' | 'pourvue' | 'fermee'

export interface Service {
  slug: ServiceSlug
  label: string
}

/** Annonce vue par la famille qui l'a publiée. */
export interface MyJob {
  id: number
  title: string
  service: Service
  availability: Availability
  budget: string | null
  location: string
  description: string
  status: JobStatus
  created_at: string
  interested_workers: number
}

/** Annonce vue par un travailleur (famille présentée par prénom + initiale). */
export interface PublicJob extends Omit<MyJob, 'interested_workers'> {
  client: { profile_id: number; name: string; rating: Rating }
}

export interface JobInput {
  title: string
  service: ServiceSlug
  availability: Availability
  budget: string | null
  location: string
  description: string
  status?: JobStatus
}

export interface Review {
  id: number
  author_name: string
  scores: Record<string, number>
  overall: string
  comment: string
  created_at: string
}

export interface ReviewsPage extends Page<Review> {
  summary: { average: string | null; count: number; criteria: Record<string, number | null> }
}

export interface InterestResponse {
  message: string
  match: { id: number; status: 'en_attente' | 'mutuel' | 'refuse' }
}
