"""
Aides pour la documentation interactive de l'API (drf-spectacular).

Nos vues renvoient souvent des réponses « enveloppées », par exemple
{"message": "Profil créé.", "profile": {...}} ou une liste paginée
{"count": …, "next": …, "previous": …, "results": [...]}. Ces fonctions
décrivent ces formats une seule fois pour toute l'API.
"""
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, inline_serializer
from rest_framework import serializers


def paginated(name, item_serializer, extra_fields=None):
    """Réponse paginée : count, next, previous, results (+ champs supplémentaires)."""
    fields = {
        **(extra_fields or {}),
        "count": serializers.IntegerField(help_text="Nombre total de résultats."),
        "next": serializers.URLField(allow_null=True, help_text="Page suivante (null si dernière)."),
        "previous": serializers.URLField(allow_null=True, help_text="Page précédente."),
        "results": item_serializer(many=True),
    }
    return inline_serializer(name=name, fields=fields)


def with_message(name, key, item_serializer):
    """Réponse du type {"message": "...", "<key>": {...}}."""
    return inline_serializer(
        name=name,
        fields={"message": serializers.CharField(), key: item_serializer()},
    )


MESSAGE_ONLY = inline_serializer(name="MessageResponse", fields={"message": serializers.CharField()})

DETAIL = inline_serializer(name="ErrorDetail", fields={"detail": serializers.CharField()})

PAGINATION_PARAMETERS = [
    OpenApiParameter("page", int, description="Numéro de page (20 résultats par page)."),
    OpenApiParameter("page_size", int, description="Taille de page personnalisée (100 maximum)."),
]


def error(description):
    """Réponse d'erreur documentée : {"detail": "..."} ou erreurs par champ."""
    return OpenApiResponse(description=description)


# Erreurs communes aux endpoints protégés
AUTH_ERRORS = {
    401: error("Token absent, invalide ou expiré (ou compte suspendu)."),
    403: error("Votre rôle (client / travailleur) n'a pas accès à cette action."),
}
