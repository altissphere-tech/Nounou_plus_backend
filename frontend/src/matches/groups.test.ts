import { describe, expect, it } from 'vitest'
import type { Match } from '../api/types'
import { groupMatches, newsCount } from './groups'

function match(id: number, fields: Partial<Match>): Match {
  return {
    id,
    status: 'en_attente',
    my_decision: 'en_attente',
    their_decision: 'en_attente',
    other_party: { id, first_name: 'X', last_name: 'Y.', photo_url: null, location: '', services_list: [], phone: null, rating: { average: null, count: 0 } },
    job: null,
    unread_count: 0,
    can_review: false,
    review_available_at: null,
    mutual_at: null,
    created_at: '',
    updated_at: '',
    ...fields,
  }
}

describe('classement des mises en relation', () => {
  const matches = [
    match(1, { status: 'mutuel', my_decision: 'interesse', their_decision: 'interesse', unread_count: 2 }),
    match(2, { their_decision: 'interesse' }), // intérêt reçu
    match(3, { my_decision: 'interesse' }), // ma demande en attente
    match(4, { status: 'refuse', my_decision: 'refuse', their_decision: 'interesse' }), // j'ai refusé
  ]

  it('range chaque mise en relation dans la bonne partie', () => {
    const groups = groupMatches(matches)
    expect(groups.mutual.map((m) => m.id)).toEqual([1])
    expect(groups.incoming.map((m) => m.id)).toEqual([2])
    expect(groups.outgoing.map((m) => m.id)).toEqual([3])
    expect(groups.declined.map((m) => m.id)).toEqual([4])
  })

  it('compte les nouveautés : intérêts reçus + messages non lus', () => {
    expect(newsCount(matches)).toBe(3)
  })
})
