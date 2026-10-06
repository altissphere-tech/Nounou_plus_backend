// Logo provisoire : sera remplacé par le logo officiel de NOUNOU+.
export default function Logo({ size = 28 }: { size?: number }) {
  return (
    <span className="logo" style={{ fontSize: size }} aria-label="NOUNOU+">
      NOUNOU<span className="logo-plus">+</span>
    </span>
  )
}
