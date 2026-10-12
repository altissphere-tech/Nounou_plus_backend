import type { ReactNode } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { useWideScreen } from '../layout/useWideScreen'

/**
 * Contenu de la page, plus une colonne d'informations à droite sur grand écran.
 * Sur téléphone et tablette, les deux enveloppes sont transparentes (display: contents) :
 * la page s'affiche exactement comme avant, et la colonne n'existe pas.
 */
export default function WithAside({ aside, children }: { aside: ReactNode; children: ReactNode }) {
  const { t } = useI18n()
  const wide = useWideScreen()
  return (
    <div className="aside-layout">
      <div className="aside-main">{children}</div>
      {wide && (
        <aside className="side-panel" aria-label={t('aside.label')}>
          {aside}
        </aside>
      )}
    </div>
  )
}
