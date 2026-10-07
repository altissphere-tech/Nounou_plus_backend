import type { ReactNode } from 'react'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

/**
 * Bandeau violet en haut d'un écran (titre, retour éventuel), comme sur la maquette.
 * `children` s'affiche sous le titre (barre de recherche, statistiques…).
 */
export default function PageHead({
  title,
  overline,
  back,
  children,
}: {
  title: ReactNode
  overline?: ReactNode
  back?: string // libellé du bouton retour (lu par les lecteurs d'écran)
  children?: ReactNode
}) {
  const navigate = useNavigate()
  return (
    <div className="page-head">
      <div className="page-head-row">
        {back && (
          <button type="button" className="icon-button" onClick={() => navigate(-1)} aria-label={back}>
            <ArrowLeft size={20} />
          </button>
        )}
        <div>
          {overline && <p className="page-head-overline">{overline}</p>}
          <h1>{title}</h1>
        </div>
      </div>
      {children}
    </div>
  )
}
