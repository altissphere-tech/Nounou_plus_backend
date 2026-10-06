import type { Availability, ServiceSlug } from '../api/types'

// Valeurs acceptées par l'API (voir /api/services/ et la documentation /api/docs/)
export const SERVICES: ServiceSlug[] = ['nounou', 'menage', 'cuisine']
export const AVAILABILITIES: Availability[] = ['temps_plein', 'temps_partiel', 'weekends']
