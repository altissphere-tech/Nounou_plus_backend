/**
 * Inscription avec e-mail + mot de passe : le compte n'est utilisable qu'après le
 * code SMS. L'e-mail et le mot de passe saisis attendent ici, en mémoire seulement
 * (jamais dans l'historique du navigateur ni sur le disque), puis sont enregistrés
 * dès que le code est validé.
 */
interface PendingCredentials {
  phone: string
  email: string
  password: string
}

let pending: PendingCredentials | null = null

export function rememberCredentials(credentials: PendingCredentials) {
  pending = credentials
}

/** Les identifiants en attente pour ce numéro (puis oubliés). */
export function takeCredentials(phone: string): PendingCredentials | null {
  const found = pending && pending.phone === phone ? pending : null
  pending = null
  return found
}
