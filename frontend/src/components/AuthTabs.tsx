import { NavLink } from 'react-router-dom'
import { useI18n } from '../i18n/I18nContext'

/** Onglets « Connexion / Inscription » en haut des écrans de connexion. */
export default function AuthTabs() {
  const { t } = useI18n()
  return (
    <nav className="segmented" aria-label={t('auth.tabs')}>
      <NavLink to="/connexion" replace>
        {t('auth.tab.login')}
      </NavLink>
      <NavLink to="/inscription" replace>
        {t('auth.tab.register')}
      </NavLink>
    </nav>
  )
}
