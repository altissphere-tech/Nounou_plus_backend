import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import OfflineScreen from './components/OfflineScreen'
import { I18nProvider, useI18n } from './i18n/I18nContext'
import Account from './pages/Account'
import Conversation from './pages/Conversation'
import Documents from './pages/Documents'
import Favorites from './pages/Favorites'
import ForgotPassword from './pages/ForgotPassword'
import Help from './pages/Help'
import Home from './pages/Home'
import JobDetail from './pages/JobDetail'
import JobForm from './pages/JobForm'
import Jobs from './pages/Jobs'
import MyJobs from './pages/MyJobs'
import Login from './pages/Login'
import Matches from './pages/Matches'
import Notifications from './pages/Notifications'
import ProfileForm from './pages/ProfileForm'
import ReportForm from './pages/ReportForm'
import ReviewForm from './pages/ReviewForm'
import Search from './pages/Search'
import Register from './pages/Register'
import ResetPassword from './pages/ResetPassword'
import Security from './pages/Security'
import SocialComplete from './pages/SocialComplete'
import Terms from './pages/Terms'
import VerifyCode from './pages/VerifyCode'
import Welcome from './pages/Welcome'
import WorkerDetail from './pages/WorkerDetail'

/**
 * Écrans réservés aux utilisateurs connectés. Sans connexion (déconnexion,
 * session expirée), retour à l'écran d'accueil qui propose de se connecter.
 */
function Private({ children }: { children: ReactNode }) {
  const { user, unreachable } = useAuth()
  const { t } = useI18n()
  if (unreachable && !user) return <OfflineScreen />
  if (user === undefined) return <p className="muted">{t('common.loading')}</p>
  return user ? children : <Navigate to="/" replace />
}

/** Écrans réservés à un rôle (famille ou travailleur) ; les autres reviennent à l'accueil. */
function OnlyFor({ role, children }: { role: 'client' | 'travailleur'; children: ReactNode }) {
  const { user } = useAuth()
  return (
    <Private>
      {user?.role === role ? children : <Navigate to="/accueil" replace />}
    </Private>
  )
}

/** Écrans d'accueil et de connexion : un utilisateur déjà connecté va directement à l'accueil. */
function Public({ children }: { children: ReactNode }) {
  const { user, unreachable } = useAuth()
  if (unreachable && !user) return <OfflineScreen />
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
              <Route path="/inscription/finaliser" element={<Public><SocialComplete /></Public>} />
              <Route path="/mot-de-passe-oublie" element={<Public><ForgotPassword /></Public>} />
              <Route path="/mot-de-passe/nouveau" element={<ResetPassword />} />
              {/* Ouverts à tous, connecté ou non */}
              <Route path="/aide" element={<Help />} />
              <Route path="/conditions" element={<Terms />} />
              <Route path="/accueil" element={<Private><Home /></Private>} />
              <Route path="/profil" element={<Private><ProfileForm /></Private>} />
              <Route path="/relations" element={<Private><Matches /></Private>} />
              <Route path="/relations/:id" element={<Private><Conversation /></Private>} />
              <Route path="/relations/:id/avis" element={<Private><ReviewForm /></Private>} />
              <Route path="/signaler/:profileId" element={<Private><ReportForm /></Private>} />
              <Route path="/compte" element={<Private><Account /></Private>} />
              <Route path="/favoris" element={<Private><Favorites /></Private>} />
              <Route path="/notifications" element={<Private><Notifications /></Private>} />
              <Route path="/securite" element={<Private><Security /></Private>} />
              <Route path="/documents" element={<OnlyFor role="travailleur"><Documents /></OnlyFor>} />
              {/* Familles */}
              <Route path="/recherche" element={<OnlyFor role="client"><Search /></OnlyFor>} />
              <Route path="/travailleurs/:id" element={<OnlyFor role="client"><WorkerDetail /></OnlyFor>} />
              <Route path="/mes-annonces" element={<OnlyFor role="client"><MyJobs /></OnlyFor>} />
              <Route path="/mes-annonces/nouvelle" element={<OnlyFor role="client"><JobForm /></OnlyFor>} />
              <Route path="/mes-annonces/:id" element={<OnlyFor role="client"><JobForm /></OnlyFor>} />
              {/* Travailleurs */}
              <Route path="/annonces" element={<OnlyFor role="travailleur"><Jobs /></OnlyFor>} />
              <Route path="/annonces/:id" element={<OnlyFor role="travailleur"><JobDetail /></OnlyFor>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  )
}
