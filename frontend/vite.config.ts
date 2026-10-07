/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import type { Plugin } from 'vite'

/**
 * Politique de sécurité du contenu (CSP) de la version finale : le navigateur
 * refuse tout script qui ne vient pas de NOUNOU+ (ou de Google / Apple pour leurs
 * boutons de connexion). Une faille XSS ne pourrait donc pas charger de code
 * extérieur pour voler une session. Ajoutée seulement au `build` : en
 * développement, Vite a besoin de scripts injectés à la volée.
 * À compléter côté hébergement par l'en-tête « frame-ancestors 'none' »
 * (impossible dans une balise meta).
 */
const CSP = [
  "default-src 'self'",
  "script-src 'self' https://accounts.google.com/gsi/client https://appleid.cdn-apple.com",
  // 'unsafe-inline' pour les styles seulement : le bouton Google en injecte
  "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style",
  "img-src 'self' data: blob: https://*.googleusercontent.com https://ssl.gstatic.com",
  "font-src 'self'",
  "connect-src 'self' https://accounts.google.com/gsi/",
  "frame-src https://accounts.google.com/gsi/ https://appleid.apple.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join('; ')

function contentSecurityPolicy(): Plugin {
  return {
    name: 'nounou-csp',
    apply: 'build',
    transformIndexHtml: (html) =>
      html.replace('<meta charset="UTF-8" />', `<meta charset="UTF-8" />\n    <meta http-equiv="Content-Security-Policy" content="${CSP}" />`),
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), contentSecurityPolicy()],
  server: {
    // En développement, les appels /api/... sont transmis au serveur Django
    // (python manage.py runserver), ce qui évite toute configuration CORS.
    // changeOrigin : Django reçoit « 127.0.0.1 » comme adresse, même quand
    // l'application est ouverte depuis un téléphone du même Wi-Fi.
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  // `npm run preview` : version finale (avec installation et mode hors connexion)
  preview: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
  },
})
