import PageHead from '../components/PageHead'
import { TERMS, TERMS_UPDATED } from '../content/terms'
import { useI18n } from '../i18n/I18nContext'

/** Conditions d'utilisation (brouillon à faire valider par un juriste). */
export default function Terms() {
  const { t, lang } = useI18n()
  const updated = new Date(TERMS_UPDATED).toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB')
  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={t('terms.title')} />
      <p className="dev-hint">{t('terms.draft')}</p>
      <p className="muted small-text">{t('terms.updated', { date: updated })}</p>
      <article className="card terms">
        {TERMS[lang].map((section) => (
          <section key={section.title}>
            <h2>{section.title}</h2>
            {section.body.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </section>
        ))}
      </article>
    </section>
  )
}
