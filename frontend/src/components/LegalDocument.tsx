import { Link } from 'react-router-dom'
import type { LegalSection } from '../content/legal'
import { useI18n } from '../i18n/I18nContext'
import PageHead from './PageHead'

const DOCUMENTS = [
  { to: '/conditions', label: 'terms.title' },
  { to: '/confidentialite', label: 'privacy.title' },
  { to: '/mentions-legales', label: 'legal.title' },
] as const

interface Props {
  title: string
  updated: string
  sections: LegalSection[]
  /** Adresse de la page affichée, pour ne pas la proposer dans « Voir aussi ». */
  path: string
}

/** Texte juridique : sections numérotées, paragraphes et listes, puis liens vers les autres textes. */
export default function LegalDocument({ title, updated, sections, path }: Props) {
  const { t, lang } = useI18n()
  const date = new Date(updated).toLocaleDateString(lang === 'fr' ? 'fr-FR' : 'en-GB')
  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={title} />
      <p className="dev-hint">{t('terms.draft')}</p>
      <p className="muted small-text">{t('terms.updated', { date })}</p>
      <article className="card terms">
        {sections.map((section) => (
          <section key={section.title}>
            <h2>{section.title}</h2>
            {section.body.map((block, index) =>
              typeof block === 'string' ? (
                <p key={index}>{block}</p>
              ) : (
                <ul key={index}>
                  {block.list.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ),
            )}
          </section>
        ))}
      </article>
      <nav className="actions" aria-label={t('legal.seeAlso')}>
        {DOCUMENTS.filter((doc) => doc.to !== path).map((doc) => (
          <Link key={doc.to} to={doc.to} className="button small secondary">
            {t(doc.label)}
          </Link>
        ))}
      </nav>
    </section>
  )
}
