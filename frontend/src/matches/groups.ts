import type { Match } from '../api/types'

export interface MatchGroups {
  mutual: Match[] // les deux sont intéressés : coordonnées visibles, messagerie ouverte
  incoming: Match[] // l'autre est intéressé, je n'ai pas encore répondu
  outgoing: Match[] // je suis intéressé, l'autre n'a pas (encore) répondu
  declined: Match[] // j'ai refusé
}

/**
 * Classe les mises en relation telles que l'API les présente à l'utilisateur.
 * Rappel : un refus de l'autre personne n'est jamais révélé (il apparaît « en attente »).
 */
export function groupMatches(matches: Match[]): MatchGroups {
  const groups: MatchGroups = { mutual: [], incoming: [], outgoing: [], declined: [] }
  for (const match of matches) {
    if (match.status === 'mutuel') groups.mutual.push(match)
    else if (match.my_decision === 'refuse') groups.declined.push(match)
    else if (match.their_decision === 'interesse' && match.my_decision === 'en_attente') groups.incoming.push(match)
    else if (match.my_decision === 'interesse') groups.outgoing.push(match)
  }
  return groups
}

/** Nombre de nouveautés à signaler : intérêts reçus + messages non lus. */
export function newsCount(matches: Match[]): number {
  const { mutual, incoming } = groupMatches(matches)
  return incoming.length + mutual.reduce((total, match) => total + match.unread_count, 0)
}

const NEWS_EVENT = 'nounou:news'

/** Demande à la barre de navigation de recompter les nouveautés (après une action). */
export function refreshNews(): void {
  window.dispatchEvent(new Event(NEWS_EVENT))
}

/** S'abonne aux demandes de recomptage. Retourne la fonction de désabonnement. */
export function onNewsRefresh(callback: () => void): () => void {
  window.addEventListener(NEWS_EVENT, callback)
  return () => window.removeEventListener(NEWS_EVENT, callback)
}
