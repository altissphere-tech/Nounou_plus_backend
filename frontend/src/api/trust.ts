import { api } from './client'
import type { ReportCategory, VerificationDocument } from './types'

// Endpoints « Vérification », « Évaluations » et « Signalements ».

export const myDocuments = () =>
  api<{ is_verified: boolean; documents: VerificationDocument[] }>('GET', '/api/verification/documents/')

export function uploadDocument(docType: string, file: File) {
  const form = new FormData()
  form.append('doc_type', docType)
  form.append('file', file)
  return api<{ document: VerificationDocument }>('POST', '/api/verification/documents/', form)
}

/** Critères notés : un client note un travailleur, un travailleur note un client. */
export const WORKER_CRITERIA = ['punctuality', 'competence', 'reliability'] as const
export const CLIENT_CRITERIA = ['respect', 'clarity', 'payment_on_time'] as const

export const sendReview = (matchId: number, scores: Record<string, number>, comment: string) =>
  api<{ message: string }>('POST', `/api/matches/${matchId}/review/`, { ...scores, comment })

export const sendReport = (profileId: number, category: ReportCategory, description: string) =>
  api<{ message: string }>('POST', '/api/reports/', { profile_id: profileId, category, description })
