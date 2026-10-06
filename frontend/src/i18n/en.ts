import type { TranslationKey } from './fr'

// English texts. Every key of fr.ts must exist here (checked by a test).
const en: Record<TranslationKey, string> = {
  'app.tagline': 'Trusted families and domestic workers in Lubumbashi',
  'lang.switch': 'Français',

  'welcome.title': 'Welcome to NOUNOU+',
  'welcome.intro':
    'Find a nanny, a housekeeper or a cook near you — or offer your services to families.',
  'welcome.register': 'Create an account',
  'welcome.login': 'I already have an account',

  'register.title': 'Create an account',
  'register.roleQuestion': 'You are…',
  'register.role.client': 'A family',
  'register.role.client.hint': 'I am looking for help at home',
  'register.role.worker': 'A domestic worker',
  'register.role.worker.hint': 'I offer my services',
  'register.submit': 'Get my code',
  'register.error': 'Could not create the account. Check the number (it may already be in use).',
  'register.haveAccount': 'I already have an account',

  'login.title': 'Log in',
  'login.submit': 'Get my code',
  'login.error': 'No account found with this number, or the account is suspended.',
  'login.noAccount': 'No account yet? Sign up',

  'phone.label': 'Phone number',
  'phone.placeholder': '081 234 5678',
  'phone.hint': 'Congolese number (+243). You will receive a code by SMS.',

  'verify.title': 'Enter your code',
  'verify.sentTo': 'Code sent to {phone}',
  'verify.label': '6-digit code',
  'verify.submit': 'Confirm',
  'verify.resend': 'Send the code again',
  'verify.resent': 'A new code has been sent.',
  'verify.error': 'Wrong code. Try again or request a new code.',
  'verify.devHint': 'Development mode: the code is always 123456.',

  'home.hello': 'Hello!',
  'home.account': 'My account',
  'home.phone': 'Phone',
  'home.role': 'I am',
  'home.role.client': 'A family',
  'home.role.travailleur': 'A domestic worker',
  'home.warnings': 'Messages from the NOUNOU+ team',
  'home.next.title': 'Next step',
  'home.next.client': 'Create your family profile to find the right person.',
  'home.next.worker': 'Create your profile to be visible to families.',
  'home.next.soon': 'Coming soon',
  'home.logout': 'Log out',

  'common.back': 'Back',
  'common.loading': 'Loading…',
  'common.networkError': 'Cannot connect. Check your internet connection.',
}

export default en
