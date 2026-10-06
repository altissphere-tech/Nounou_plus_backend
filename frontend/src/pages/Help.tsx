import { Mail, MessageCircle, Phone } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import PageHead from '../components/PageHead'
import { CONTACT, CONTACT_IS_PLACEHOLDER } from '../content/contact'
import { FAQ } from '../content/help'
import { useI18n } from '../i18n/I18nContext'

/** Écran « Aide & support » : questions fréquentes et coordonnées de l'équipe. */
export default function Help() {
  const { t, lang } = useI18n()
  const { user } = useAuth()
  return (
    <section className="stack">
      <PageHead back={t('common.back')} title={t('help.title')} />

      <h2 className="overline">{t('help.faq')}</h2>
      <div className="faq">
        {FAQ[lang].map((item) => (
          <details key={item.q} className="card faq-item">
            <summary>{item.q}</summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>

      <h2 className="overline">{t('help.contact')}</h2>
      <div className="card">
        {CONTACT_IS_PLACEHOLDER && <p className="dev-hint">{t('help.placeholder')}</p>}
        <p className="contact-line">
          <Mail size={18} aria-hidden="true" /> {CONTACT.email}
        </p>
        <p className="contact-line">
          <Phone size={18} aria-hidden="true" /> {CONTACT.phone}
        </p>
        <p className="contact-line">
          <MessageCircle size={18} aria-hidden="true" /> WhatsApp : {CONTACT.whatsapp}
        </p>
        <p className="muted small-text">
          {CONTACT.hours[lang]} · {CONTACT.address}
        </p>
      </div>

      <div className="actions">
        <Link to="/conditions" className="button small secondary">
          {t('terms.title')}
        </Link>
        {user && (
          <Link to="/securite" className="button small secondary">
            {t('security.title')}
          </Link>
        )}
      </div>
    </section>
  )
}
