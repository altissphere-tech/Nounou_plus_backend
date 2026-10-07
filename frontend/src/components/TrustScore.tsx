import { Check, Clock } from 'lucide-react'
import type { Trust } from '../api/types'
import { useI18n } from '../i18n/I18nContext'

/**
 * « Score de confiance » : les contrôles réellement faits par NOUNOU+.
 * Téléphone : confirmé par code SMS. Identité : pièce validée par l'équipe.
 * Références : au moins une personne appelée par l'équipe a confirmé.
 */
export default function TrustScore({ trust }: { trust: Trust }) {
  const { t } = useI18n()
  const steps = [
    { key: 'trust.phone', done: trust.phone },
    { key: 'trust.identity', done: trust.identity },
    { key: 'trust.references', done: trust.references },
  ] as const
  return (
    <div className="trust">
      <h2 className="overline">{t('trust.title')}</h2>
      <ul className="trust-steps">
        {steps.map((step) => (
          <li key={step.key} className={step.done ? 'done' : ''}>
            <span className="trust-dot">{step.done ? <Check size={16} strokeWidth={3} /> : <Clock size={16} />}</span>
            {t(step.key)}
            <span className="visually-hidden">{step.done ? t('trust.done') : t('trust.notYet')}</span>
          </li>
        ))}
      </ul>
      {trust.identity && <p className="trust-note">{t('worker.verifiedNote')}</p>}
    </div>
  )
}
