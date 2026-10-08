import { Component, Suspense } from 'react'
import type { ReactNode } from 'react'
import PageSkeleton from '../components/PageSkeleton'
import { useI18n } from '../i18n/I18nContext'

/** Message si un écran n'a pas pu être téléchargé (réseau coupé pendant le chargement). */
function LoadFailed() {
  const { t } = useI18n()
  return (
    <div className="card stack" role="alert">
      <p>{t('screen.loadFailed')}</p>
      <button type="button" className="button primary" onClick={() => window.location.reload()}>
        {t('screen.retry')}
      </button>
    </div>
  )
}

class LoadErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    return this.state.failed ? <LoadFailed /> : this.props.children
  }
}

/** Pendant le téléchargement d'un écran : sa silhouette ; en cas d'échec : un message clair. */
export default function ScreenBoundary({ children, resetKey }: { children: ReactNode; resetKey: string }) {
  return (
    // Clé = adresse de l'écran : en changeant d'écran, on retente le téléchargement
    <LoadErrorBoundary key={resetKey}>
      <Suspense fallback={<PageSkeleton />}>{children}</Suspense>
    </LoadErrorBoundary>
  )
}
