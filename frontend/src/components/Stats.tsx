/** Rangée de chiffres clés (expérience, tarif, note…) sous l'en-tête d'une fiche. */
export default function Stats({ items }: { items: { label: string; value: string; accent?: boolean }[] }) {
  return (
    <dl className="stats">
      {items.map((item) => (
        <div key={item.label} className="stat">
          <dt>{item.label}</dt>
          <dd className={item.accent ? 'accent' : ''}>{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
