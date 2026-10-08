import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * À chaque nouvel écran (comme dans une application) :
 * - la page repart en haut ;
 * - le titre de l'onglet prend celui de l'écran (« Mes relations · NOUNOU+ ») ;
 * - au clavier et avec un lecteur d'écran, la lecture reprend au titre du nouvel
 *   écran au lieu de rester sur le lien qui vient d'être touché.
 */
export default function ScrollToTop() {
  const { pathname } = useLocation()
  const firstScreen = useRef(true)

  useEffect(() => {
    window.scrollTo(0, 0)
    const main = document.getElementById('contenu')
    if (!main) return
    const moveFocus = !firstScreen.current
    firstScreen.current = false

    // L'écran peut s'afficher un peu plus tard (téléchargé à la demande) : on attend son titre
    const apply = () => {
      const heading = main.querySelector('h1')
      if (!heading) return false
      document.title = `${heading.textContent?.trim()} · NOUNOU+`
      if (moveFocus) {
        heading.setAttribute('tabindex', '-1')
        heading.focus({ preventScroll: true })
      }
      return true
    }
    if (apply()) return
    const observer = new MutationObserver(() => {
      if (apply()) observer.disconnect()
    })
    observer.observe(main, { childList: true, subtree: true })
    const stop = window.setTimeout(() => observer.disconnect(), 5000)
    return () => {
      observer.disconnect()
      window.clearTimeout(stop)
    }
  }, [pathname])
  return null
}
