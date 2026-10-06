import { useI18n } from '../i18n/I18nContext'

/** Champ de saisie du numéro de téléphone (le serveur accepte « 081… » ou « +243… »). */
export default function PhoneField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const { t } = useI18n()
  return (
    <label className="field">
      <span className="field-label">{t('phone.label')}</span>
      <input
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        required
        placeholder={t('phone.placeholder')}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <span className="field-hint">{t('phone.hint')}</span>
    </label>
  )
}
