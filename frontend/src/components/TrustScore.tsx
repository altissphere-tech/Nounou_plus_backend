import { Check, Clock } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

/**
 * « Score de confiance » : les contrôles réellement faits par NOUNOU+.
 * Le téléphone est confirmé par code SMS à l'inscription ; l'identité par l'équipe.
 */
export default function TrustScore({ verified }: { verified: boolean }) {
  const { t } = useI18n()
  const steps = [
    { key: 'trust.phone', done: true },
    { key: 'trust.identity', done: verified },
  ] as const
  return (
    <div className="trust">
      <h2 className="overline">{t('trust.title')}</h2>
      <ul className="trust-steps">
        {steps.map((step) => (
          <li key={step.key} className={step.done ? 'done' : ''}>
            <span className="trust-dot">{step.done ? <Check size={16} strokeWidth={3} /> : <Clock size={16} />}</span>
            {t(step.key)}
          </li>
        ))}
      </ul>
      <p className="trust-note">{verified ? t('worker.verifiedNote') : t('trust.pending')}</p>
    </div>
  )
}
