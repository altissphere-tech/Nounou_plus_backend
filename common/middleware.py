"""
En-têtes de sécurité ajoutés aux réponses de l'API (en plus de ceux de Django :
X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Cross-Origin-Opener-Policy).

- Content-Security-Policy stricte : une réponse de l'API (JSON, photo) ne doit
  jamais pouvoir exécuter de script ni être affichée dans un cadre.
- Cache-Control « no-store » : les données personnelles de l'API ne sont gardées
  ni par le navigateur ni par un proxy (téléphone partagé, cybercafé). Exception :
  les photos validées, publiques par nature.
- Permissions-Policy : l'API n'a besoin d'aucun accès (caméra, micro, position…).
"""
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        if request.path.startswith("/api/") and not request.path.startswith(("/api/docs/", "/api/redoc/")):
            response.setdefault("Content-Security-Policy", API_CSP)
            if not request.path.startswith("/api/photos/"):
                response["Cache-Control"] = "no-store"
        return response
