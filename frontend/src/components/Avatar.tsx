/**
 * Pastille ronde avec les initiales (les profils n'ont pas encore de photo).
 * La couleur dépend du nom, pour distinguer les personnes d'un coup d'œil.
 */
const COLORS = ['#3B12B8', '#7C3AED', '#F5931E', '#0E9F6E', '#D9468F', '#2563EB']

export default function Avatar({ name, size = 48 }: { name: string; size?: number }) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join('')
  const hash = [...name].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return (
    <span
      className="avatar"
      aria-hidden="true"
      style={{ width: size, height: size, fontSize: size * 0.38, background: COLORS[hash % COLORS.length] }}
    >
      {initials}
    </span>
  )
}
