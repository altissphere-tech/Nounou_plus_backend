import type { Language } from '../i18n/I18nContext'
import { CONTACT } from './contact'

/**
 * Mentions légales et Politique de confidentialité de NOUNOU+.
 *
 * Texte fourni par le fondateur le 8 octobre 2026, vérifié et ajusté pour décrire
 * exactement ce que fait l'application (voir docs/MENTIONS_LEGALES.md : liste des
 * corrections). Si une fonctionnalité change (paiement, localisation, statistiques,
 * cookies…), ces textes doivent être mis à jour en même temps.
 * La version française fait foi ; l'anglaise est une traduction.
 */

export const COMPANY = {
  name: 'ALTIS SPHERE GROUP SARL',
  form: { fr: 'Société à responsabilité limitée de droit congolais', en: 'Limited liability company under Congolese law' },
  address: {
    fr: '110, avenue Biayi, quartier Kalubwe, Lubumbashi, République démocratique du Congo',
    en: '110 Avenue Biayi, Kalubwe district, Lubumbashi, Democratic Republic of the Congo',
  },
  rccm: 'CD/LSH/RCCM/26-B-00091',
  idNat: '01-71-N32130B',
  nif: 'A 1810067N',
}

/** Hébergeur de la version en ligne : à préciser au moment de la mise en ligne (docs/DEPLOIEMENT.md). */
export const HOSTING_PROVIDER: string | null = null

export const PRIVACY_UPDATED = '2026-10-08'
export const LEGAL_UPDATED = '2026-10-08'

/** Un paragraphe, ou une liste à puces. */
export type LegalBlock = string | { list: string[] }

export interface LegalSection {
  title: string
  body: LegalBlock[]
}

/** « Libellé : valeur », avec la ponctuation de chaque langue. */
const line = (lang: Language, label: string, value: string) => `${label}${lang === 'fr' ? ' : ' : ': '}${value}`

const identity = (lang: Language): string[] => [
    COMPANY.name,
    COMPANY.form[lang],
    line(lang, lang === 'fr' ? 'Siège social' : 'Registered office', COMPANY.address[lang]),
    line(lang, 'RCCM', COMPANY.rccm),
    line(lang, 'ID. NAT.', COMPANY.idNat),
    line(lang, 'NIF', COMPANY.nif),
]

/** E-mail et téléphone du support (l'adresse figure déjà dans l'identité de la société). */
const supportLines = (lang: Language): string[] => [
  line(lang, lang === 'fr' ? 'E-mail' : 'Email', CONTACT.email),
  line(lang, lang === 'fr' ? 'Téléphone / WhatsApp' : 'Phone / WhatsApp', CONTACT.phone),
]

const contactLines = (lang: Language): string[] => [
  line(lang, lang === 'fr' ? 'Adresse' : 'Address', COMPANY.address[lang]),
  ...supportLines(lang),
]

const hosting = (lang: Language) =>
  HOSTING_PROVIDER ??
  (lang === 'fr' ? 'précisé ici au moment de la mise en ligne' : 'to be stated here when the service goes live')

// --------------------------------------------------------------------------
// Mentions légales
// --------------------------------------------------------------------------

export const LEGAL_NOTICE: Record<Language, LegalSection[]> = {
  fr: [
    {
      title: '1. Éditeur et exploitant',
      body: [
        'La plateforme NOUNOU+ est éditée, développée et exploitée par :',
        { list: identity('fr') },
        'Ci-après « ALTIS SPHERE GROUP », « la Société », « nous », « notre » ou « nos ». ALTIS SPHERE GROUP est responsable de l’exploitation de NOUNOU+ et de son fonctionnement général, dans les limites prévues par les Conditions d’utilisation.',
      ],
    },
    {
      title: '2. La plateforme NOUNOU+',
      body: [
        'NOUNOU+ est une plateforme numérique de mise en relation entre des familles qui recherchent une aide à domicile et des travailleurs domestiques (nounous, aides ménagères, cuisinières) à Lubumbashi. Elle permet notamment de :',
        { list: [
          'créer et gérer un compte ;',
          'présenter son profil et consulter les profils des autres utilisateurs ;',
          'rechercher des travailleurs et publier ou consulter des annonces ;',
          'manifester son intérêt et, en cas d’accord mutuel, échanger des messages et ses coordonnées ;',
          'laisser un avis après une période d’essai et signaler un comportement inapproprié ;',
          'accéder à d’autres fonctionnalités proposées ultérieurement.',
        ] },
        'Les fonctionnalités disponibles peuvent évoluer avec le développement de la plateforme.',
      ],
    },
    {
      title: '3. Rôle de NOUNOU+',
      body: [
        'NOUNOU+ agit en qualité de plateforme de mise en relation. ALTIS SPHERE GROUP n’est pas l’employeur des travailleurs : le contrat de travail (salaire, horaires, congés) est conclu directement entre la famille et le travailleur.',
        'Les travailleurs restent responsables des informations qu’ils communiquent, de leurs qualifications, de leurs disponibilités et de l’exécution de leur travail. Les familles restent responsables des informations qu’elles fournissent et de leurs engagements envers les travailleurs. Les vérifications réalisées par l’équipe NOUNOU+ (badge « Vérifié ») ne constituent pas une garantie.',
      ],
    },
    {
      title: '4. Contact',
      body: [
        'Pour toute question sur NOUNOU+, son utilisation, les Conditions d’utilisation ou votre compte :',
        { list: contactLines('fr') },
        'Toute modification de ces coordonnées sera indiquée sur la plateforme.',
      ],
    },
    {
      title: '5. Propriété intellectuelle',
      body: [
        'La plateforme NOUNOU+, son nom, sa marque, son identité visuelle, ses interfaces, ses textes, ses logiciels et ses bases de données sont protégés par le droit de la propriété intellectuelle. Sauf indication contraire, ils appartiennent à ALTIS SPHERE GROUP SARL ou font l’objet de droits d’utilisation accordés à celle-ci.',
        'Toute reproduction, modification, extraction ou exploitation, totale ou partielle, sans autorisation écrite préalable est interdite. L’utilisation de la plateforme ne confère aucun droit de propriété sur celle-ci.',
      ],
    },
    {
      title: '6. Hébergement',
      body: [
        `La plateforme est hébergée sur les serveurs d’un fournisseur d’infrastructure choisi par ALTIS SPHERE GROUP : ${hosting('fr')}. Les échanges entre votre appareil et NOUNOU+ sont chiffrés (HTTPS).`,
      ],
    },
    {
      title: '7. Données personnelles',
      body: [
        'La collecte et l’utilisation de vos données sont décrites dans la Politique de confidentialité de NOUNOU+, qui fait partie du cadre contractuel applicable (lien ci-dessous).',
      ],
    },
    {
      title: '8. Acceptation',
      body: [
        'En utilisant NOUNOU+ ou en créant un compte, vous reconnaissez avoir pris connaissance des présentes mentions légales, des Conditions d’utilisation et de la Politique de confidentialité. Ces informations peuvent être mises à jour pour tenir compte de l’évolution de la société, de la plateforme ou de la réglementation.',
      ],
    },
  ],
  en: [
    {
      title: '1. Publisher and operator',
      body: [
        'The NOUNOU+ platform is published, developed and operated by:',
        { list: identity('en') },
        'Hereinafter “ALTIS SPHERE GROUP”, “the Company”, “we”, “our” or “us”. ALTIS SPHERE GROUP is responsible for operating NOUNOU+ and for its general functioning, within the limits set by the Terms of use.',
      ],
    },
    {
      title: '2. The NOUNOU+ platform',
      body: [
        'NOUNOU+ is a digital platform connecting families looking for help at home with domestic workers (nannies, housekeepers, cooks) in Lubumbashi. It notably lets you:',
        { list: [
          'create and manage an account;',
          'present your profile and view other users’ profiles;',
          'search for workers and publish or browse job posts;',
          'show interest and, after a mutual agreement, exchange messages and contact details;',
          'leave a review after a trial period and report inappropriate behaviour;',
          'use other features offered in the future.',
        ] },
        'Available features may change as the platform develops.',
      ],
    },
    {
      title: '3. Role of NOUNOU+',
      body: [
        'NOUNOU+ acts as a matching platform. ALTIS SPHERE GROUP is not the employer of the workers: the employment contract (salary, hours, leave) is agreed directly between the family and the worker.',
        'Workers remain responsible for the information they provide, their qualifications, availability and work. Families remain responsible for the information they provide and their commitments to workers. Checks made by the NOUNOU+ team (“Verified” badge) are not a guarantee.',
      ],
    },
    {
      title: '4. Contact',
      body: [
        'For any question about NOUNOU+, its use, the Terms of use or your account:',
        { list: contactLines('en') },
        'Any change to these details will be shown on the platform.',
      ],
    },
    {
      title: '5. Intellectual property',
      body: [
        'The NOUNOU+ platform, its name, brand, visual identity, interfaces, texts, software and databases are protected by intellectual property law. Unless stated otherwise, they belong to ALTIS SPHERE GROUP SARL or are used under rights granted to it.',
        'Any full or partial reproduction, modification, extraction or use without prior written permission is forbidden. Using the platform grants no ownership right over it.',
      ],
    },
    {
      title: '6. Hosting',
      body: [
        `The platform is hosted on the servers of an infrastructure provider chosen by ALTIS SPHERE GROUP: ${hosting('en')}. Exchanges between your device and NOUNOU+ are encrypted (HTTPS).`,
      ],
    },
    {
      title: '7. Personal data',
      body: [
        'How your data is collected and used is described in the NOUNOU+ Privacy policy, which is part of the applicable contractual framework (link below).',
      ],
    },
    {
      title: '8. Acceptance',
      body: [
        'By using NOUNOU+ or creating an account, you acknowledge that you have read this legal notice, the Terms of use and the Privacy policy. This information may be updated to reflect changes to the company, the platform or regulations.',
      ],
    },
  ],
}

// --------------------------------------------------------------------------
// Politique de confidentialité
// --------------------------------------------------------------------------

export const PRIVACY: Record<Language, LegalSection[]> = {
  fr: [
    {
      title: 'Objet',
      body: [
        'La présente Politique explique comment ALTIS SPHERE GROUP SARL, exploitant de NOUNOU+, collecte, utilise, conserve, protège et, le cas échéant, partage les données personnelles des utilisateurs. Elle s’applique au site web, à l’application installable (PWA), aux applications mobiles lorsqu’elles seront disponibles et à tout service numérique exploité sous la marque NOUNOU+.',
      ],
    },
    {
      title: '1. Responsable du traitement',
      body: [{ list: [...identity('fr'), ...supportLines('fr')] }],
    },
    {
      title: '2. Données que nous collectons',
      body: [
        'Nous ne collectons que les données nécessaires au service.',
        'Pour tous les utilisateurs :',
        { list: [
          'numéro de téléphone (obligatoire, confirmé par code SMS) ;',
          'adresse e-mail et mot de passe (facultatifs ; le mot de passe est stocké sous forme chiffrée irréversible, jamais en clair) ;',
          'identifiant Google ou Apple, si vous choisissez cette connexion ;',
          'prénom, nom et quartier ;',
          'photo de profil (facultative) ;',
          'messages échangés, avis et signalements.',
        ] },
        'Pour une famille : services recherchés, disponibilité souhaitée, budget, description des besoins et annonces publiées.',
        'Pour un travailleur : services proposés, expérience, disponibilité, salaire souhaité, présentation, pièce d’identité et autres justificatifs envoyés pour la vérification, et références (nom, téléphone et lien de chaque personne de référence, avec son accord).',
        'Nous ne collectons pas la date de naissance, le sexe, la position GPS de l’appareil, ni aucune donnée bancaire.',
      ],
    },
    {
      title: '3. Données collectées automatiquement',
      body: [
        'Pour la sécurité et le bon fonctionnement du service, nos serveurs enregistrent des journaux techniques : adresse IP, date et heure, type de navigateur, ainsi que les événements de sécurité (connexions, échecs, codes refusés, limites d’essais atteintes). Les adresses e-mail et numéros de téléphone n’y figurent que sous une forme codée, jamais les mots de passe ni les codes.',
        'NOUNOU+ n’utilise aucun outil de statistiques ou de publicité et ne suit pas les pages que vous consultez.',
      ],
    },
    {
      title: '4. Pourquoi nous utilisons vos données',
      body: [
        { list: [
          'Créer et sécuriser votre compte, vous authentifier (codes SMS, e-mail, Google / Apple).',
          'Permettre la mise en relation entre familles et travailleurs, la messagerie et les avis.',
          'Vérifier l’identité et les références des travailleurs, à leur demande.',
          'Prévenir la fraude et les abus, traiter les signalements et modérer les contenus.',
          'Répondre à vos demandes adressées au support.',
          'Corriger les erreurs et améliorer le service.',
          'Respecter nos obligations légales ou répondre à une demande d’une autorité compétente.',
        ] },
      ],
    },
    {
      title: '5. Base du traitement',
      body: [
        'Selon les cas : la fourniture du service que vous demandez et l’exécution des Conditions d’utilisation ; votre consentement lorsqu’il est requis (que vous pouvez retirer à tout moment, sans effet sur les traitements déjà réalisés) ; la sécurité des utilisateurs et de la plateforme ; le respect des obligations légales ; les intérêts légitimes de la Société, lorsque le droit applicable le permet.',
      ],
    },
    {
      title: '6. Ce que voient les autres utilisateurs',
      body: [
        'Avant un accord mutuel, les autres utilisateurs voient seulement : votre prénom et l’initiale de votre nom, votre quartier, les informations de votre profil (services, expérience, disponibilité, salaire ou budget, présentation), votre photo une fois validée par l’équipe, votre statut de vérification et vos avis.',
        'Votre nom complet et votre numéro de téléphone ne sont communiqués à l’autre personne qu’après un accord mutuel (les deux personnes se sont déclarées intéressées). Un refus n’est jamais signalé à l’autre personne.',
        'Les annonces et besoins des familles ne sont visibles que des travailleurs dont le profil a été vérifié par l’équipe.',
        'Les pièces d’identité, justificatifs et coordonnées des références ne sont jamais visibles par les autres utilisateurs : seule l’équipe NOUNOU+ y a accès.',
      ],
    },
    {
      title: '7. Localisation',
      body: [
        'NOUNOU+ n’utilise pas la position GPS de votre appareil. Seul le quartier que vous indiquez sert à la recherche et à l’affichage des profils. Si une fonction de localisation est ajoutée plus tard, votre autorisation sera demandée par votre téléphone et cette Politique sera mise à jour.',
      ],
    },
    {
      title: '8. Paiement',
      body: [
        'NOUNOU+ ne propose aucun paiement : la plateforme ne perçoit pas les salaires et ne collecte aucune donnée bancaire ou de Mobile Money. Si un paiement est ajouté plus tard, le prestataire choisi et les données concernées seront indiqués ici avant sa mise en service.',
      ],
    },
    {
      title: '9. Partage des données',
      body: [
        'ALTIS SPHERE GROUP ne vend pas vos données. Elles peuvent être communiquées, uniquement lorsque c’est nécessaire :',
        { list: [
          'aux utilisateurs avec qui vous êtes en relation, dans les limites décrites à la section 6 ;',
          'aux membres de l’équipe NOUNOU+ chargés de la vérification, de la modération et du support : ils peuvent consulter les documents, les références et, en cas de signalement ou pour la sécurité, les messages échangés ;',
          'à nos prestataires techniques : hébergement, envoi des codes SMS, envoi des e-mails, et Google ou Apple si vous utilisez leur connexion ;',
          'aux autorités compétentes lorsque la loi l’exige.',
        ] },
        'Chaque prestataire ne reçoit que les données nécessaires à sa mission.',
      ],
    },
    {
      title: '10. Hébergement',
      body: [
        `Les données sont hébergées sur les serveurs d’un fournisseur d’infrastructure choisi par ALTIS SPHERE GROUP : ${hosting('fr')}. Les échanges sont chiffrés (HTTPS) et la base de données n’est pas accessible depuis Internet.`,
      ],
    },
    {
      title: '11. Sécurité',
      body: [
        'Nous appliquons des mesures raisonnables et adaptées, notamment :',
        { list: [
          'chiffrement des communications (HTTPS / TLS) ;',
          'confirmation du numéro de téléphone par code SMS, codes à usage unique valables 10 minutes ;',
          'mots de passe stockés sous forme chiffrée irréversible ;',
          'déconnexion automatique après 30 minutes d’inactivité et possibilité de se déconnecter de tous les appareils ;',
          'accès aux documents et données sensibles limité à l’équipe ;',
          'limitation des essais, journal des événements de sécurité, sauvegardes et mises à jour de sécurité.',
        ] },
        'Aucun système connecté à Internet ne peut être garanti totalement sans risque. En cas d’incident de sécurité touchant vos données, nous prendrons les mesures appropriées conformément au droit applicable.',
      ],
    },
    {
      title: '12. Durée de conservation',
      body: [
        { list: [
          'Données du compte : pendant toute la durée d’utilisation du compte.',
          'Codes SMS : effacés dès leur utilisation, et au plus tard inutilisables après 10 minutes.',
          'Photo refusée par l’équipe : supprimée immédiatement.',
          'Journaux techniques et de sécurité : durée limitée, nécessaire à la sécurité et à l’administration du service.',
          'Après la fermeture d’un compte : certaines données peuvent être conservées lorsque c’est nécessaire pour une obligation légale, la prévention de la fraude, la sécurité ou un litige.',
        ] },
      ],
    },
    {
      title: '13. Suppression du compte',
      body: [
        `Vous pouvez demander la suppression de votre compte en écrivant à ${CONTACT.email}. La demande est traitée dans un délai raisonnable, après vérification de votre identité. La suppression n’entraîne pas nécessairement l’effacement immédiat de toutes les données dans les cas prévus à la section 12.`,
      ],
    },
    {
      title: '14. Vos droits',
      body: [
        'Dans les limites prévues par le droit applicable, vous pouvez demander : l’accès à vos données, leur correction, leur suppression, la limitation de certains traitements, vous opposer à certains traitements, retirer votre consentement, ou obtenir des informations sur l’utilisation de vos données. Beaucoup de ces informations sont modifiables directement dans l’application (profil, photo, e-mail, mot de passe).',
        'Écrivez au support (coordonnées en section 1) en précisant votre demande et le numéro de téléphone du compte. Pour protéger votre compte, nous pouvons vous demander de prouver votre identité.',
      ],
    },
    {
      title: '15. Communications',
      body: [
        'NOUNOU+ vous envoie uniquement les messages nécessaires au service : codes de vérification par SMS, e-mails de confirmation d’adresse ou de mot de passe oublié, et notifications dans l’application (intérêt reçu, accord mutuel, messages, décisions de l’équipe).',
        'NOUNOU+ n’envoie pas de messages publicitaires. Si cela change, votre accord sera demandé au préalable et vous pourrez vous désabonner à tout moment.',
      ],
    },
    {
      title: '16. Cookies et stockage sur l’appareil',
      body: [
        'L’application n’utilise ni cookie publicitaire, ni cookie de statistiques. Elle garde sur votre appareil uniquement ce qui est nécessaire à son fonctionnement : vos jetons de connexion, votre langue, certains choix d’affichage, et une copie des écrans de l’application pour l’ouverture sans connexion (jamais vos données personnelles).',
        'L’espace d’administration réservé à l’équipe utilise des cookies de session et de sécurité indispensables.',
      ],
    },
    {
      title: '17. Données des travailleurs',
      body: [
        'Les informations professionnelles des travailleurs (services, expérience, quartier, disponibilité, salaire souhaité, présentation, photo validée, statut de vérification et avis) sont visibles par les familles, dans les limites de la section 6. Les travailleurs sont responsables de l’exactitude de ces informations.',
        'Le badge « Vérifié » signifie que l’équipe a contrôlé les documents fournis. Il ne constitue pas une garantie sur la qualité, le comportement ou le travail futur de la personne.',
      ],
    },
    {
      title: '18. Mineurs',
      body: [
        'NOUNOU+ est réservé aux personnes âgées d’au moins 18 ans (voir les Conditions d’utilisation). Les informations concernant des enfants (par exemple leur âge dans la description des besoins) doivent être fournies par leur parent ou représentant légal et limitées au strict nécessaire. Un compte créé en violation de cette règle peut être suspendu.',
      ],
    },
    {
      title: '19. Services tiers',
      body: [
        'Si vous utilisez la connexion Google ou Apple, ou si vous ouvrez un lien vers un service tiers (WhatsApp, appel téléphonique), le traitement de vos données par ces services relève de leur propre politique de confidentialité.',
      ],
    },
    {
      title: '20. Transferts hors de la RDC',
      body: [
        'Certains prestataires techniques (hébergement, envoi de SMS ou d’e-mails, connexion Google / Apple) peuvent traiter des données en dehors de la République démocratique du Congo. ALTIS SPHERE GROUP prend alors les mesures appropriées prévues par le droit applicable. La liste des principaux prestataires sera publiée ici avant la mise en ligne.',
      ],
    },
    {
      title: '21. Modifications',
      body: [
        'Cette Politique peut être modifiée pour tenir compte de l’évolution de NOUNOU+, de nouvelles fonctionnalités ou de la réglementation. La date de dernière mise à jour figure en haut de la page. En cas de changement important, vous en serez informé dans l’application.',
      ],
    },
    {
      title: '22. Contact',
      body: [
        'Pour toute question, demande ou réclamation concernant vos données personnelles :',
        { list: [COMPANY.name, ...contactLines('fr')] },
      ],
    },
    {
      title: '23. Entrée en vigueur',
      body: [
        'La présente Politique entre en vigueur à sa date de publication sur NOUNOU+. En utilisant NOUNOU+, vous reconnaissez en avoir pris connaissance dans les conditions prévues par les Conditions d’utilisation.',
      ],
    },
  ],
  en: [
    {
      title: 'Purpose',
      body: [
        'This Policy explains how ALTIS SPHERE GROUP SARL, operator of NOUNOU+, collects, uses, stores, protects and, where applicable, shares users’ personal data. It applies to the website, the installable app (PWA), mobile apps when available and any digital service operated under the NOUNOU+ brand. The French version prevails.',
      ],
    },
    {
      title: '1. Data controller',
      body: [{ list: [...identity('en'), ...supportLines('en')] }],
    },
    {
      title: '2. Data we collect',
      body: [
        'We only collect the data needed for the service.',
        'For all users:',
        { list: [
          'phone number (required, confirmed by SMS code);',
          'email address and password (optional; the password is stored in an irreversibly encrypted form, never in clear text);',
          'Google or Apple identifier, if you choose that sign-in;',
          'first name, last name and neighbourhood;',
          'profile photo (optional);',
          'messages, reviews and reports.',
        ] },
        'For a family: services sought, desired availability, budget, description of needs and published job posts.',
        'For a worker: services offered, experience, availability, expected salary, introduction, ID document and other proofs sent for verification, and references (name, phone and relationship of each referee, with their consent).',
        'We do not collect date of birth, sex, the device’s GPS position, or any banking data.',
      ],
    },
    {
      title: '3. Data collected automatically',
      body: [
        'For security and proper operation, our servers keep technical logs: IP address, date and time, browser type, and security events (sign-ins, failures, rejected codes, attempt limits reached). Email addresses and phone numbers only appear in coded form, never passwords or codes.',
        'NOUNOU+ uses no analytics or advertising tool and does not track the pages you view.',
      ],
    },
    {
      title: '4. Why we use your data',
      body: [
        { list: [
          'Create and secure your account, sign you in (SMS codes, email, Google / Apple).',
          'Connect families and workers, enable messaging and reviews.',
          'Check workers’ identity and references, at their request.',
          'Prevent fraud and abuse, handle reports and moderate content.',
          'Answer your requests to support.',
          'Fix errors and improve the service.',
          'Comply with legal obligations or requests from competent authorities.',
        ] },
      ],
    },
    {
      title: '5. Legal basis',
      body: [
        'Depending on the case: providing the service you request and performing the Terms of use; your consent where required (which you can withdraw at any time, without affecting earlier processing); the safety of users and the platform; compliance with legal obligations; the Company’s legitimate interests, where applicable law allows.',
      ],
    },
    {
      title: '6. What other users see',
      body: [
        'Before a mutual agreement, other users only see: your first name and last-name initial, your neighbourhood, your profile information (services, experience, availability, salary or budget, introduction), your photo once approved by the team, your verification status and your reviews.',
        'Your full name and phone number are shared with the other person only after a mutual agreement (both people said they were interested). A decline is never revealed to the other person.',
        'Families’ job posts and needs are only visible to workers whose profile has been verified by the team.',
        'ID documents, proofs and referees’ contact details are never visible to other users: only the NOUNOU+ team can access them.',
      ],
    },
    {
      title: '7. Location',
      body: [
        'NOUNOU+ does not use your device’s GPS position. Only the neighbourhood you enter is used for search and profile display. If a location feature is added later, your phone will ask for your permission and this Policy will be updated.',
      ],
    },
    {
      title: '8. Payment',
      body: [
        'NOUNOU+ offers no payment: the platform does not collect salaries or any banking or Mobile Money data. If payment is added later, the chosen provider and the data concerned will be listed here before it goes live.',
      ],
    },
    {
      title: '9. Sharing data',
      body: [
        'ALTIS SPHERE GROUP does not sell your data. It may be shared, only when necessary:',
        { list: [
          'with users you are connected with, within the limits described in section 6;',
          'with NOUNOU+ team members in charge of verification, moderation and support: they may view documents, references and, in case of a report or for safety, exchanged messages;',
          'with our technical providers: hosting, sending SMS codes, sending emails, and Google or Apple if you use their sign-in;',
          'with competent authorities when required by law.',
        ] },
        'Each provider only receives the data needed for its task.',
      ],
    },
    {
      title: '10. Hosting',
      body: [
        `Data is hosted on the servers of an infrastructure provider chosen by ALTIS SPHERE GROUP: ${hosting('en')}. Exchanges are encrypted (HTTPS) and the database is not reachable from the Internet.`,
      ],
    },
    {
      title: '11. Security',
      body: [
        'We apply reasonable and appropriate measures, including:',
        { list: [
          'encrypted communications (HTTPS / TLS);',
          'phone number confirmed by SMS code, single-use codes valid for 10 minutes;',
          'passwords stored in irreversibly encrypted form;',
          'automatic sign-out after 30 minutes of inactivity and the option to sign out of all devices;',
          'access to documents and sensitive data restricted to the team;',
          'attempt limits, security event log, backups and security updates.',
        ] },
        'No system connected to the Internet can be guaranteed completely risk-free. If a security incident affects your data, we will take appropriate measures in accordance with applicable law.',
      ],
    },
    {
      title: '12. Retention',
      body: [
        { list: [
          'Account data: for as long as the account is used.',
          'SMS codes: erased once used, and unusable after 10 minutes at most.',
          'Photo rejected by the team: deleted immediately.',
          'Technical and security logs: a limited period needed for security and administration.',
          'After an account is closed: some data may be kept when needed for a legal obligation, fraud prevention, security or a dispute.',
        ] },
      ],
    },
    {
      title: '13. Deleting your account',
      body: [
        `You can ask for your account to be deleted by writing to ${CONTACT.email}. The request is handled within a reasonable time, after checking your identity. Deletion does not necessarily mean all data is erased immediately in the cases listed in section 12.`,
      ],
    },
    {
      title: '14. Your rights',
      body: [
        'Within the limits of applicable law, you can ask to access, correct or delete your data, to restrict or object to some processing, to withdraw your consent, or to get information about how your data is used. Much of this information can be changed directly in the app (profile, photo, email, password).',
        'Write to support (details in section 1) stating your request and the account’s phone number. To protect your account, we may ask you to prove your identity.',
      ],
    },
    {
      title: '15. Communications',
      body: [
        'NOUNOU+ only sends messages needed for the service: SMS verification codes, emails to confirm your address or reset your password, and in-app notifications (interest received, mutual agreement, messages, team decisions).',
        'NOUNOU+ sends no advertising. If this changes, your consent will be asked first and you will be able to unsubscribe at any time.',
      ],
    },
    {
      title: '16. Cookies and on-device storage',
      body: [
        'The app uses no advertising or analytics cookies. It only keeps on your device what it needs to work: your sign-in tokens, your language, some display choices, and a copy of the app’s screens for offline opening (never your personal data).',
        'The administration area reserved for the team uses essential session and security cookies.',
      ],
    },
    {
      title: '17. Workers’ data',
      body: [
        'Workers’ professional information (services, experience, neighbourhood, availability, expected salary, introduction, approved photo, verification status and reviews) is visible to families, within the limits of section 6. Workers are responsible for its accuracy.',
        'The “Verified” badge means the team has checked the documents provided. It is not a guarantee of the person’s quality, behaviour or future work.',
      ],
    },
    {
      title: '18. Minors',
      body: [
        'NOUNOU+ is reserved for people aged 18 or over (see the Terms of use). Information about children (for example their age in a description of needs) must be given by their parent or legal guardian and kept to the strict minimum. An account created in breach of this rule may be suspended.',
      ],
    },
    {
      title: '19. Third-party services',
      body: [
        'If you use Google or Apple sign-in, or open a link to a third-party service (WhatsApp, phone call), their processing of your data is governed by their own privacy policy.',
      ],
    },
    {
      title: '20. Transfers outside the DRC',
      body: [
        'Some technical providers (hosting, SMS or email sending, Google / Apple sign-in) may process data outside the Democratic Republic of the Congo. ALTIS SPHERE GROUP then takes the appropriate measures required by applicable law. The list of main providers will be published here before launch.',
      ],
    },
    {
      title: '21. Changes',
      body: [
        'This Policy may change to reflect changes to NOUNOU+, new features or regulations. The last update date is shown at the top of the page. You will be informed in the app of any important change.',
      ],
    },
    {
      title: '22. Contact',
      body: [
        'For any question, request or complaint about your personal data:',
        { list: [COMPANY.name, ...contactLines('en')] },
      ],
    },
    {
      title: '23. Entry into force',
      body: [
        'This Policy takes effect on its publication date on NOUNOU+. By using NOUNOU+, you acknowledge that you have read it under the conditions set by the Terms of use.',
      ],
    },
  ],
}
