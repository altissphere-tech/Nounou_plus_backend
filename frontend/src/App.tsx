import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import { I18nProvider, useI18n } from './i18n/I18nContext'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import VerifyCode from './pages/VerifyCode'
import Welcome from './pages/Welcome'

/**
 * Écrans réservés aux utilisateurs connectés. Sans connexion (déconnexion,
 * session expirée), retour à l'écran d'accueil qui propose de se connecter.
 */
function Private({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const { t } = useI18n()
  if (user === undefined) return <p className="muted">{t('common.loading')}</p>
  return user ? children : <Navigate to="/" replace />
}

/** Écrans d'accueil et de connexion : un utilisateur déjà connecté va directement à l'accueil. */
function Public({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (user === undefined) return null
  return user ? <Navigate to="/accueil" replace /> : children
}

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Public><Welcome /></Public>} />
              <Route path="/inscription" element={<Public><Register /></Public>} />
              <Route path="/connexion" element={<Public><Login /></Public>} />
              <Route path="/code" element={<Public><VerifyCode /></Public>} />
              <Route path="/accueil" element={<Private><Home /></Private>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  )
}
