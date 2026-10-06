import { api } from './client'
import type {
  InterestResponse,
  JobInput,
  MyJob,
  Page,
  PublicJob,
  PublicWorker,
  ReviewsPage,
} from './types'

/** Construit « ?service=nounou&location=golf » en ignorant les filtres vides. */
export function queryString(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const text = query.toString()
  return text ? `?${text}` : ''
}

/** Les liens « page suivante » de l'API sont complets : on garde le chemin + la requête. */
export function relativeUrl(url: string): string {
  const parsed = new URL(url, window.location.origin)
  return parsed.pathname + parsed.search
}

export const fetchPage = <T>(url: string) => api<Page<T>>('GET', relativeUrl(url))

// --- Travailleurs (familles) -------------------------------------------------

export interface WorkerFilters {
  service?: string
  location?: string
  availability?: string
  max_salary?: string
  min_experience?: string
  ordering?: string
}

export const searchWorkers = (filters: WorkerFilters) =>
  api<Page<PublicWorker>>('GET', `/api/workers/${queryString({ ...filters })}`)

export const getWorker = (id: number) => api<PublicWorker>('GET', `/api/workers/${id}/`)

export const getWorkerReviews = (id: number) => api<ReviewsPage>('GET', `/api/reviews/workers/${id}/`)

/** « Je suis intéressé(e) » par un profil (travailleur pour une famille, famille pour un travailleur). */
export const expressInterest = (profileId: number) =>
  api<InterestResponse>('POST', '/api/matches/interest/', { profile_id: profileId })

// --- Annonces ----------------------------------------------------------------

export interface JobFilters {
  service?: string
  location?: string
  availability?: string
  min_budget?: string
}

export const searchJobs = (filters: JobFilters) =>
  api<Page<PublicJob>>('GET', `/api/jobs/${queryString({ ...filters })}`)

export const getJob = <T extends MyJob | PublicJob>(id: number) => api<T>('GET', `/api/jobs/${id}/`)

export const myJobs = () => api<Page<MyJob>>('GET', '/api/jobs/mine/')

export const createJob = (data: JobInput) => api<{ job: MyJob }>('POST', '/api/jobs/', data)

export const updateJob = (id: number, data: Partial<JobInput>) =>
  api<{ job: MyJob }>('PATCH', `/api/jobs/${id}/`, data)

export const applyToJob = (id: number) => api<InterestResponse>('POST', `/api/jobs/${id}/interest/`)
