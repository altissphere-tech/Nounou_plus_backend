/** Remplace les {variables} d'un texte. Ex : interpolate('Code envoyé au {phone}', {phone: '…'}) */
export function interpolate(text: string, params?: Record<string, string>): string {
  if (!params) return text
  return text.replace(/\{(\w+)\}/g, (match, name) => params[name] ?? match)
}
