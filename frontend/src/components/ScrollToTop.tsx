import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Chaque nouvel écran s'ouvre en haut de la page (comme dans une application). */
export default function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}
