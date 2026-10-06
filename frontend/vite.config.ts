/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
