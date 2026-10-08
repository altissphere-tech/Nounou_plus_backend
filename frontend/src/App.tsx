import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import OfflineScreen from './components/OfflineScreen'
import { I18nProvider, useI18n } from './i18n/I18nContext'
import Welcome from './pages/Welcome'
import { lazyScreen } from './routing/lazyScreen'
import ScreenBoundary from './routing/ScreenBoundary'

// Écran d'accueil des visiteurs : dans le fichier principal (affichage immédiat).
// Les autres sont téléchargés à l'ouverture (voir routing/lazyScreen.ts).
const Account = lazyScreen(() => import('./pages/Account'))
const ConfirmEmail = lazyScreen(() => import('./pages/ConfirmEmail'))
const Conversation = lazyScreen(() => import('./pages/Conversation'))
const Documents = lazyScreen(() => import('./pages/Documents'))
const Favorites = lazyScreen(() => import('./pages/Favorites'))
const ForgotPassword = lazyScreen(() => import('./pages/ForgotPassword'))
const Help = lazyScreen(() => import('./pages/Help'))
const Home = lazyScreen(() => import('./pages/Home'))
const JobDetail = lazyScreen(() => import('./pages/JobDetail'))
const JobForm = lazyScreen(() => import('./pages/JobForm'))
const Jobs = lazyScreen(() => import('./pages/Jobs'))
const MyJobs = lazyScreen(() => import('./pages/MyJobs'))
const Matches = lazyScreen(() => import('./pages/Matches'))
const Notifications = lazyScreen(() => import('./pages/Notifications'))
const ProfileForm = lazyScreen(() => import('./pages/ProfileForm'))
const ReportForm = lazyScreen(() => import('./pages/ReportForm'))
const ReviewForm = lazyScreen(() => import('./pages/ReviewForm'))
const Search = lazyScreen(() => import('./pages/Search'))
const ResetPassword = lazyScreen(() => import('./pages/ResetPassword'))
const Security = lazyScreen(() => import('./pages/Security'))
const SocialComplete = lazyScreen(() => import('./pages/SocialComplete'))
const Terms = lazyScreen(() => import('./pages/Terms'))
const WorkerDetail = lazyScreen(() => import('./pages/WorkerDetail'))
const VerifyCode = lazyScreen(() => import('./pages/VerifyCode'))
const Register = lazyScreen(() => import('./pages/Register'))
const Login = lazyScreen(() => import('./pages/Login'))

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
            <Screens />
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  )
}

function Screens() {
  const { pathname } = useLocation()
  return (
    <ScreenBoundary resetKey={pathname}>
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
              <Route path="/email/confirmer" element={<ConfirmEmail />} />
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
    </ScreenBoundary>
  )
}
