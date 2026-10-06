import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/fr'

export default function Home() {
  const { t } = useI18n()
  const { user, logout } = useAuth()
  if (!user) return null

  const isClient = user.role === 'client'
  return (
    <section className="stack">
      <h1>{t('home.hello')}</h1>

      {user.warnings.length > 0 && (
        <div className="card warning">
          <h2>{t('home.warnings')}</h2>
          {user.warnings.map((w) => (
            <p key={w.date}>{w.message}</p>
          ))}
        </div>
      )}

      <div className="card">
        <h2>{t('home.next.title')}</h2>
        <p>{isClient ? t('home.next.client') : t('home.next.worker')}</p>
        <span className="badge">{t('home.next.soon')}</span>
      </div>

      <div className="card">
        <h2>{t('home.account')}</h2>
        <dl className="details">
          <dt>{t('home.phone')}</dt>
          <dd>{user.phone}</dd>
          <dt>{t('home.role')}</dt>
          <dd>{t(`home.role.${user.role}` as TranslationKey)}</dd>
        </dl>
        <button type="button" className="button secondary" onClick={logout}>
          {t('home.logout')}
        </button>
      </div>
    </section>
  )
}
