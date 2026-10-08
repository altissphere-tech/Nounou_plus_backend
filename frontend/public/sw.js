/*
 * Service worker NOUNOU+ : permet d'installer l'application et de l'ouvrir
 * même avec une connexion lente ou coupée.
 *
 * Règle importante : les réponses de l'API (/api/), de l'admin et des fichiers
 * envoyés ne sont JAMAIS gardées en mémoire — seulement les fichiers de
 * l'application (écrans, styles, icônes). Les données personnelles viennent
 * toujours du serveur.
 *
 * Après une modification de ce fichier, augmentez VERSION pour remplacer l'ancien cache.
 */
const VERSION = 'nounou-v3'
const SHELL = ['/', '/manifest.webmanifest', '/logo.webp', '/bg-nounou.svg', '/favicon.png', '/icons/icon-192.png']
const NEVER_CACHED = ['/api/', '/admin/', '/media/', '/static/']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)))
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin) return
  if (NEVER_CACHED.some((prefix) => url.pathname.startsWith(prefix))) return

  if (request.mode === 'navigate') {
    // Écrans : on essaie le réseau (version la plus récente), sinon la copie gardée
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Seule une vraie page de l'application remplace la copie gardée : jamais une
          // page d'erreur, un document (PDF, image) ni une page « à ne pas garder »
          // (administration, quelle que soit son adresse).
          const type = response.headers.get('content-type') || ''
          const cacheControl = response.headers.get('cache-control') || ''
          if (response.ok && type.startsWith('text/html') && !/no-store|private/.test(cacheControl)) {
            const copy = response.clone()
            caches.open(VERSION).then((cache) => cache.put('/', copy))
          }
          return response
        })
        .catch(() => caches.match('/')),
    )
    return
  }

  // Fichiers de l'application (noms uniques à chaque version) : la copie gardée d'abord
  event.respondWith(
    caches.match(request).then(
      (cached) =>
        cached ||
        fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(VERSION).then((cache) => cache.put(request, copy))
          }
          return response
        }),
    ),
  )
})
