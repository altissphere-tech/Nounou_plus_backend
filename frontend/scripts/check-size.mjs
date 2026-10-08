// Limite de poids de l'application (budget) : vérifiée par GitHub à chaque demande de fusion.
// Ce qui se télécharge à la première ouverture doit rester léger pour la 3G à Lubumbashi.
// Usage : npm run build && npm run size
import { readFileSync } from 'node:fs'
import { gzipSync } from 'node:zlib'

const BUDGET_KB = {
  js: 105, // JavaScript chargé à l'ouverture (compressé) — 128 Ko avant le découpage par écran
  css: 9, // Styles (compressés)
}

const html = readFileSync('dist/index.html', 'utf8')
const files = [...html.matchAll(/(?:src|href)="\/(assets\/[^"]+\.(js|css))"/g)]
let failed = false
for (const kind of ['js', 'css']) {
  const total = files
    .filter(([, , ext]) => ext === kind)
    .reduce((sum, [, path]) => sum + gzipSync(readFileSync(`dist/${path}`)).length, 0) / 1024
  const ok = total <= BUDGET_KB[kind]
  failed ||= !ok
  console.log(`${ok ? '✓' : '✗'} ${kind.toUpperCase()} à l'ouverture : ${total.toFixed(1)} Ko (limite ${BUDGET_KB[kind]} Ko)`)
}
if (failed) {
  console.error("L'application est devenue trop lourde : téléchargez à la demande ou allégez avant d'augmenter la limite.")
  process.exit(1)
}
