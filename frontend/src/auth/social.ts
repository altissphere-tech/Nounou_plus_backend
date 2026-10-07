/**
 * Connexion Google / Apple dans le navigateur.
 *
 * Google et Apple fournissent un petit programme (chargé depuis leurs sites) qui
 * ouvre leur fenêtre de connexion et renvoie un « jeton d'identité ». Ce jeton est
 * ensuite vérifié par le serveur NOUNOU+. Aucun mot de passe ne passe par NOUNOU+.
 */
import { getAuthOptions } from '../api/accounts'
import type { AuthOptions } from '../api/types'

let optionsPromise: Promise<AuthOptions> | null = null

/** Moyens de connexion activés sur le serveur (demandés une seule fois). */
export function authOptions(): Promise<AuthOptions> {
  optionsPromise ??= getAuthOptions().catch((error) => {
    optionsPromise = null
    throw error
  })
  return optionsPromise
}

const loaded = new Map<string, Promise<void>>()

function loadScript(src: string): Promise<void> {
  if (!loaded.has(src)) {
    loaded.set(
      src,
      new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = src
        script.async = true
        script.onload = () => resolve()
        script.onerror = () => {
          loaded.delete(src)
          reject(new Error(`script ${src}`))
        }
        document.head.appendChild(script)
      }),
    )
  }
  return loaded.get(src)!
}

// Types minimaux des programmes de Google et d'Apple
interface GoogleId {
  initialize(config: { client_id: string; callback: (response: { credential: string }) => void }): void
  renderButton(element: HTMLElement, options: Record<string, unknown>): void
}
interface AppleId {
  init(config: Record<string, unknown>): void
  signIn(): Promise<{ authorization: { id_token: string } }>
}
declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } }
    AppleID?: { auth: AppleId }
  }
}

/** Affiche le bouton officiel Google dans `element` ; `onToken` reçoit le jeton. */
export async function renderGoogleButton(
  element: HTMLElement,
  clientId: string,
  lang: string,
  onToken: (token: string) => void,
): Promise<void> {
  await loadScript('https://accounts.google.com/gsi/client')
  const google = window.google!.accounts.id
  google.initialize({ client_id: clientId, callback: (response) => onToken(response.credential) })
  google.renderButton(element, {
    theme: 'outline',
    size: 'large',
    shape: 'pill',
    text: 'continue_with',
    locale: lang,
    width: element.clientWidth || 300,
  })
}

/** Ouvre la fenêtre « Se connecter avec Apple » et renvoie le jeton. */
export async function signInWithApple(clientId: string): Promise<string> {
  await loadScript('https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js')
  const apple = window.AppleID!.auth
  apple.init({
    clientId,
    scope: 'email',
    redirectURI: `${window.location.origin}/connexion`,
    usePopup: true,
  })
  const response = await apple.signIn()
  return response.authorization.id_token
}
