/**
 * Logo officiel NOUNOU+ : l'icône (maison violette + « + » orange)
 * suivie du nom, avec le « + » dans l'orange de la marque.
 */
export default function Logo({ size = 28, withName = true }: { size?: number; withName?: boolean }) {
  return (
    <span className="logo" style={{ fontSize: size * 0.8 }}>
      <img src="/logo.webp" alt="" width={size} height={size} className="logo-icon" />
      {withName && (
        <span className="logo-name">
          NOUNOU<span className="logo-plus">+</span>
        </span>
      )}
      {!withName && <span className="visually-hidden">NOUNOU+</span>}
    </span>
  )
}
