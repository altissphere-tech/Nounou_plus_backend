/**
 * Coordonnées affichées dans « Aide » et « Conditions d'utilisation ».
 * Seule la raison sociale exacte reste à compléter par le fondateur.
 */
export const CONTACT = {
  company: 'ALTIS Sphere Group (raison sociale à compléter)',
  email: 'support@nounou-plus.com',
  phone: '+243 998 914 448',
  whatsapp: '+243 998 914 448',
  address: '110, av. Biayi, Kalubwe, Lubumbashi, RD Congo',
  hours: { fr: 'Lundi à samedi, 8 h – 18 h', en: 'Monday to Saturday, 8 am – 6 pm' },
}

/** Numéros sans espaces, pour les liens « appeler » et WhatsApp. */
export const CONTACT_PHONE_DIGITS = '243998914448'

/** true tant que des coordonnées affichées dans « Aide » sont provisoires (bandeau « à compléter »). */
export const CONTACT_IS_PLACEHOLDER = false
