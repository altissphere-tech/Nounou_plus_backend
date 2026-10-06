import type { Language } from '../i18n/I18nContext'

/** Questions fréquentes de l'écran « Aide & support ». */
export const FAQ: Record<Language, { q: string; a: string }[]> = {
  fr: [
    {
      q: 'Comment fonctionne NOUNOU+ ?',
      a: "Les familles cherchent un profil ou publient une annonce ; les travailleurs répondent aux annonces. Quand les deux personnes sont intéressées, c'est un « match » : leurs noms complets et numéros deviennent visibles et la messagerie s'ouvre.",
    },
    {
      q: 'Que signifie le badge « Vérifié » ?',
      a: "L'équipe NOUNOU+ a contrôlé la pièce d'identité du travailleur. Le score de confiance montre aussi si son téléphone est confirmé et si une référence a été vérifiée. Ce n'est pas une garantie d'absence de risque : faites toujours un entretien et une période d'essai.",
    },
    {
      q: 'Quand puis-je voir le numéro de téléphone de quelqu’un ?',
      a: "Seulement après un accord mutuel (match). Avant, vous voyez le prénom, l'initiale du nom, le quartier et le profil.",
    },
    {
      q: "Ma photo n'apparaît pas pour les autres",
      a: "Chaque photo est vérifiée par l'équipe avant d'être visible. Vous recevez une notification quand elle est validée ou refusée (avec le motif).",
    },
    {
      q: "J'ai oublié mon mot de passe",
      a: "Sur l'écran de connexion, touchez « Mot de passe oublié ? » et indiquez votre e-mail : vous recevrez un lien. Vous pouvez aussi toujours vous connecter avec votre numéro de téléphone et un code SMS.",
    },
    {
      q: 'Comment ajouter des références ? (travailleurs)',
      a: "Dans « Mon compte » → « Vérification », ajoutez jusqu'à 3 personnes (ancien employeur, voisin…). L'équipe les appelle ; leurs coordonnées ne sont jamais montrées aux familles.",
    },
    {
      q: 'Comment signaler un problème ?',
      a: "Sur chaque profil et chaque mise en relation, touchez « Signaler ce profil ». Le signalement est anonyme. En cas de danger immédiat, contactez d'abord les autorités.",
    },
  ],
  en: [
    {
      q: 'How does NOUNOU+ work?',
      a: "Families search for profiles or post jobs; workers respond to jobs. When both people are interested, it's a “match”: full names and phone numbers become visible and chat opens.",
    },
    {
      q: 'What does the “Verified” badge mean?',
      a: 'The NOUNOU+ team checked the worker’s ID document. The trust score also shows whether their phone is confirmed and whether a reference was checked. It is not a guarantee that there is no risk: always hold an interview and a trial period.',
    },
    {
      q: 'When can I see someone’s phone number?',
      a: 'Only after you both agree (a match). Before that, you see the first name, last-name initial, neighbourhood and profile.',
    },
    {
      q: 'My photo is not visible to others',
      a: 'Every photo is reviewed by the team before it becomes visible. You get a notification when it is approved or declined (with the reason).',
    },
    {
      q: 'I forgot my password',
      a: 'On the login screen, tap “Forgot password?” and enter your email: you will receive a link. You can also always log in with your phone number and an SMS code.',
    },
    {
      q: 'How do I add references? (workers)',
      a: 'In “My account” → “Verification”, add up to 3 people (former employer, neighbour…). The team calls them; their contact details are never shown to families.',
    },
    {
      q: 'How do I report a problem?',
      a: 'On every profile and match, tap “Report this profile”. Reports are anonymous. If you are in immediate danger, contact the authorities first.',
    },
  ],
}
