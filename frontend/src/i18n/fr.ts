// Textes de l'application en français (langue par défaut).
// Chaque clé doit aussi exister dans en.ts (vérifié par un test).
const fr = {
  'app.tagline': 'Familles et travailleurs domestiques de confiance à Lubumbashi',
  'lang.switch': 'English',

  'welcome.title': 'Bienvenue sur NOUNOU+',
  'welcome.intro':
    'Trouvez une nounou, une aide ménagère ou une cuisinière près de chez vous — ou proposez vos services aux familles.',
  'welcome.register': 'Créer un compte',
  'welcome.login': "J'ai déjà un compte",

  'register.title': 'Créer un compte',
  'register.roleQuestion': 'Vous êtes…',
  'register.role.client': 'Une famille',
  'register.role.client.hint': "Je cherche de l'aide à domicile",
  'register.role.worker': 'Un travailleur / une travailleuse',
  'register.role.worker.hint': 'Je propose mes services',
  'register.submit': 'Recevoir mon code',
  'register.error': "Impossible de créer le compte. Vérifiez le numéro (il est peut-être déjà utilisé).",
  'register.haveAccount': "J'ai déjà un compte",

  'login.title': 'Se connecter',
  'login.submit': 'Recevoir mon code',
  'login.error': 'Aucun compte trouvé avec ce numéro, ou compte suspendu.',
  'login.noAccount': 'Pas encore de compte ? Inscrivez-vous',

  'phone.label': 'Numéro de téléphone',
  'phone.placeholder': '081 234 5678',
  'phone.hint': 'Numéro congolais (+243). Vous recevrez un code par SMS.',

  'verify.title': 'Entrez votre code',
  'verify.sentTo': 'Code envoyé au {phone}',
  'verify.label': 'Code à 6 chiffres',
  'verify.submit': 'Valider',
  'verify.resend': 'Renvoyer le code',
  'verify.resent': 'Un nouveau code a été envoyé.',
  'verify.error': 'Code incorrect. Réessayez ou demandez un nouveau code.',
  'verify.devHint': 'Mode développement : le code est toujours 123456.',

  'home.hello': 'Bonjour !',
  'home.account': 'Mon compte',
  'home.phone': 'Téléphone',
  'home.role': 'Je suis',
  'home.role.client': 'Une famille',
  'home.role.travailleur': 'Un travailleur / une travailleuse',
  'home.warnings': "Messages de l'équipe NOUNOU+",
  'home.next.title': 'Prochaine étape',
  'home.next.client': 'Créez votre profil famille pour trouver la bonne personne.',
  'home.next.worker': 'Créez votre profil pour être visible des familles.',
  'home.next.soon': 'Bientôt disponible',
  'home.logout': 'Se déconnecter',

  'common.back': 'Retour',
  'common.loading': 'Chargement…',
  'common.networkError': 'Connexion impossible. Vérifiez votre connexion internet.',
} as const

export default fr
export type TranslationKey = keyof typeof fr
