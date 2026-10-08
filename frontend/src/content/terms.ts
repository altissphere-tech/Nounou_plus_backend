import type { Language } from '../i18n/I18nContext'
import { CONTACT } from './contact'
import { COMPANY } from './legal'

/**
 * Conditions d'utilisation — BROUILLON préparé pour le fondateur.
 * ⚠️ Doit être relu et validé par un juriste (droit congolais) avant la mise en ligne.
 */
export const TERMS_UPDATED = '2026-10-08'

export const TERMS: Record<Language, { title: string; body: string[] }[]> = {
  fr: [
    {
      title: '1. Objet',
      body: [
        `NOUNOU+ est un service de mise en relation entre des familles et des travailleurs domestiques (nounous, aides ménagères, cuisinières) à Lubumbashi. Il est édité par ${CONTACT.company}.`,
      ],
    },
    {
      title: '2. Rôle de NOUNOU+',
      body: [
        "NOUNOU+ est un intermédiaire : il n'est pas l'employeur des travailleurs. Le contrat de travail (salaire, horaires, congés) est conclu directement entre la famille et le travailleur, dans le respect du Code du travail de la République démocratique du Congo.",
        'NOUNOU+ ne perçoit pas les salaires et ne demande jamais de paiement à un travailleur pour obtenir un emploi.',
      ],
    },
    {
      title: '3. Inscription et compte',
      body: [
        "Il faut avoir au moins 18 ans, donner des informations exactes et n'avoir qu'un seul compte. Le numéro de téléphone est obligatoire : c'est lui qui est partagé après un accord mutuel.",
        'Vous êtes responsable de la confidentialité de votre mot de passe et des codes reçus par SMS. Ne les communiquez à personne, même à quelqu’un qui dit travailler pour NOUNOU+.',
      ],
    },
    {
      title: '4. Vérifications et badge « Vérifié »',
      body: [
        "L'équipe NOUNOU+ contrôle les pièces d'identité, les photos de profil et, sur demande des travailleurs, leurs références. Le badge « Vérifié » et le score de confiance indiquent ces contrôles.",
        "Ils ne constituent pas une garantie d'absence de risque. Chaque famille et chaque travailleur reste responsable de ses choix : entretien, période d'essai, vérifications complémentaires.",
      ],
    },
    {
      title: '5. Données personnelles',
      body: [
        'Données collectées : numéro de téléphone, e-mail (facultatif), nom, quartier, informations du profil, photo, documents de vérification, références, messages.',
        "Avant un accord mutuel, les autres utilisateurs voient seulement votre prénom, l'initiale de votre nom, votre quartier, votre profil et votre photo validée. Votre nom complet et votre téléphone ne sont partagés qu'après un accord mutuel.",
        "Les documents de vérification et les coordonnées des références ne sont vus que par l'équipe NOUNOU+. Vous pouvez demander l'accès à vos données, leur correction ou la suppression de votre compte en écrivant au support.",
        'Le détail (données collectées, partage, conservation, vos droits) figure dans la Politique de confidentialité, qui fait partie des présentes conditions.',
      ],
    },
    {
      title: '6. Règles de conduite',
      body: [
        "Sont interdits : faux profils, harcèlement, propos discriminatoires, demandes d'argent avant une embauche, partage des coordonnées d'autrui sans son accord, et toute activité illégale.",
      ],
    },
    {
      title: '7. Signalements et sanctions',
      body: [
        "Chacun peut signaler un profil, de façon anonyme. Après examen, l'équipe peut classer le signalement, avertir la personne ou suspendre son compte.",
      ],
    },
    {
      title: '8. Responsabilité',
      body: [
        "NOUNOU+ met tout en œuvre pour la qualité du service mais ne peut être tenu responsable des relations de travail entre utilisateurs, ni des informations fausses données par un utilisateur.",
      ],
    },
    {
      title: '9. Modification des conditions',
      body: [
        "Ces conditions peuvent évoluer. Les utilisateurs sont informés des changements importants dans l'application.",
      ],
    },
    {
      title: '10. Contact',
      body: [`${CONTACT.company} — ${CONTACT.address} — RCCM ${COMPANY.rccm} — ${CONTACT.email} — ${CONTACT.phone}`],
    },
  ],
  en: [
    {
      title: '1. Purpose',
      body: [
        `NOUNOU+ is a service that connects families and domestic workers (nannies, housekeepers, cooks) in Lubumbashi. It is published by ${CONTACT.company}.`,
      ],
    },
    {
      title: '2. Role of NOUNOU+',
      body: [
        'NOUNOU+ is an intermediary: it is not the employer of the workers. The employment contract (salary, hours, leave) is agreed directly between the family and the worker, in accordance with the Labour Code of the Democratic Republic of the Congo.',
        'NOUNOU+ does not collect salaries and never asks a worker for payment to get a job.',
      ],
    },
    {
      title: '3. Registration and account',
      body: [
        'You must be at least 18, give accurate information and have only one account. A phone number is required: it is what gets shared after a mutual agreement.',
        'You are responsible for keeping your password and SMS codes secret. Never share them, even with someone claiming to work for NOUNOU+.',
      ],
    },
    {
      title: '4. Checks and “Verified” badge',
      body: [
        'The NOUNOU+ team checks ID documents, profile photos and, when workers provide them, their references. The “Verified” badge and the trust score reflect these checks.',
        'They are not a guarantee that there is no risk. Every family and worker remains responsible for their choices: interview, trial period, further checks.',
      ],
    },
    {
      title: '5. Personal data',
      body: [
        'Data collected: phone number, email (optional), name, neighbourhood, profile information, photo, verification documents, references, messages.',
        'Before a mutual agreement, other users only see your first name, last-name initial, neighbourhood, profile and approved photo. Your full name and phone number are shared only after a mutual agreement.',
        'Verification documents and references’ contact details are only seen by the NOUNOU+ team. You can ask to access or correct your data, or to delete your account, by writing to support.',
        'Details (data collected, sharing, retention, your rights) are in the Privacy policy, which is part of these terms.',
      ],
    },
    {
      title: '6. Code of conduct',
      body: [
        'Forbidden: fake profiles, harassment, discriminatory remarks, asking for money before hiring, sharing other people’s contact details without consent, and any illegal activity.',
      ],
    },
    {
      title: '7. Reports and sanctions',
      body: [
        'Anyone can report a profile anonymously. After review, the team may dismiss the report, warn the person or suspend their account.',
      ],
    },
    {
      title: '8. Liability',
      body: [
        'NOUNOU+ does its best to provide a quality service but cannot be held liable for employment relationships between users, or for false information given by a user.',
      ],
    },
    {
      title: '9. Changes to these terms',
      body: ['These terms may change. Users are informed of important changes in the app.'],
    },
    {
      title: '10. Contact',
      body: [`${CONTACT.company} — ${CONTACT.address} — RCCM ${COMPANY.rccm} — ${CONTACT.email} — ${CONTACT.phone}`],
    },
  ],
}
