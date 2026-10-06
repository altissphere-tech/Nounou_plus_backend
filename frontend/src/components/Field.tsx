import { cloneElement, useId } from 'react'
import type { ReactElement } from 'react'

/**
 * Champ de formulaire : étiquette + saisie + texte d'aide.
 * L'aide est reliée au champ (aria-describedby) sans faire partie de son nom,
 * ce qui reste clair pour les lecteurs d'écran.
 */
export default function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: ReactElement<{ id?: string; 'aria-describedby'?: string }>
}) {
  const id = useId()
  const hintId = `${id}-hint`
  return (
    <div className="field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      {cloneElement(children, { id, 'aria-describedby': hint ? hintId : undefined })}
      {hint && (
        <span className="field-hint" id={hintId}>
          {hint}
        </span>
      )}
    </div>
  )
}
