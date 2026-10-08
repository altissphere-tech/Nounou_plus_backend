import { useState } from 'react'

/**
 * Photo de profil ronde, ou pastille avec les initiales s'il n'y a pas de photo
 * validée. La couleur dépend du nom, pour distinguer les personnes d'un coup d'œil
 * (6 couleurs du design system : --avatar-1 à --avatar-6).
 */
const COLOR_COUNT = 6

export default function Avatar({ name, size = 48, src }: { name: string; size?: number; src?: string | null }) {
  const [broken, setBroken] = useState<string | null>(null)
  if (src && broken !== src) {
    return (
      <img
        className="avatar"
        src={src}
        alt=""
        width={size}
        height={size}
        style={{ width: size, height: size }}
        onError={() => setBroken(src)}
      />
    )
  }
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
      style={{ width: size, height: size, fontSize: size * 0.38, background: `var(--avatar-${(hash % COLOR_COUNT) + 1})` }}
    >
      {initials}
    </span>
  )
}
