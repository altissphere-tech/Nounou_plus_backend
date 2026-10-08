// Formats renvoyés par l'API (voir la documentation interactive : /api/docs/).

export type Role = 'client' | 'travailleur' | 'admin'

export type PhotoStatus = 'aucune' | 'en_attente' | 'validee' | 'rejetee'
export type SocialProvider = 'google' | 'apple'

export interface User {
  id: number
  phone: string
  role: Role
  phone_verified: boolean
  email: string | null
  email_verified: boolean
  /** Adresse saisie, en attente du clic sur le lien de confirmation. */
  pending_email: string
  has_password: boolean
  social_providers: SocialProvider[]
  photo_status: PhotoStatus
  photo_rejection_reason: string
  created_at: string
}

export interface AuthOptions {
  sms: boolean
  google_client_id: string
  apple_client_id: string
}

/** Contrôles faits par NOUNOU+ (ce n'est pas une garantie d'absence de risque). */
export interface Trust {
  phone: boolean
  identity: boolean
  references: boolean
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
  photo_url: string | null
  bio: string
  services_list: ServiceSlug[]
  years_experience: number
  availability: Availability
  expected_salary: string
  location: string
  is_verified: boolean
  trust: Trust
  rating: Rating
  phone_display: string
}

export interface ClientProfile {
  id: number
  first_name: string
  last_name: string
  photo_url: string | null
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
  client: { profile_id: number; name: string; photo_url: string | null; rating: Rating }
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

export type Decision = 'en_attente' | 'interesse' | 'refuse'
export type MatchStatus = 'en_attente' | 'mutuel' | 'refuse'

/** L'autre personne d'une mise en relation : nom complet et téléphone seulement si match mutuel. */
export interface OtherParty {
  id: number // identifiant de son profil (travailleur ou client)
  first_name: string
  last_name: string
  photo_url: string | null
  location: string
  services_list: ServiceSlug[]
  phone: string | null
  rating: Rating
}

export interface Match {
  id: number
  status: MatchStatus
  my_decision: Decision
  their_decision: Decision
  other_party: OtherParty
  job: { id: number; title: string } | null
  unread_count: number
  can_review: boolean
  review_available_at: string | null
  mutual_at: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  content: string
  is_mine: boolean
  is_hidden: boolean
  read_at: string | null
  created_at: string
}

export type DocType = 'identite' | 'reference'
export type DocStatus = 'en_attente' | 'valide' | 'rejete'

export interface VerificationDocument {
  id: number
  doc_type: DocType
  status: DocStatus
  rejection_reason: string
  reviewed_at: string | null
  created_at: string
}

export type ReportCategory = 'faux_profil' | 'comportement_inapproprie' | 'arnaque' | 'securite' | 'autre'

export type ReferenceStatus = 'en_attente' | 'verifiee' | 'non_confirmee'

export interface WorkerReference {
  id: number
  name: string
  phone: string
  relationship: string
  status: ReferenceStatus
  reviewed_at: string | null
  created_at: string
}

export type NotificationKind =
  | 'interest_received'
  | 'match_mutual'
  | 'new_message'
  | 'document_reviewed'
  | 'photo_reviewed'
  | 'reference_reviewed'
  | 'warning'

export interface AppNotification {
  id: number
  kind: NotificationKind
  params: {
    match_id?: number
    name?: string
    approved?: boolean
    reason?: string
    doc_type?: DocType
  }
  count: number
  is_read: boolean
  created_at: string
}

export interface Favorites {
  workers: PublicWorker[]
  jobs: PublicJob[]
}
