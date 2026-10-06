import { useI18n } from '../i18n/I18nContext'
import Field from './Field'

/** Champ de saisie du numéro de téléphone (le serveur accepte « 081… » ou « +243… »). */
export default function PhoneField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const { t } = useI18n()
  return (
    <Field label={t('phone.label')} hint={t('phone.hint')}>
      <input
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        required
        placeholder={t('phone.placeholder')}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </Field>
  )
}
