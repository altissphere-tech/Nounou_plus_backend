"""
Pagination partagée : les listes sont découpées en pages de 20 éléments.

Paramètres d'URL :
- ?page=2          → deuxième page
- ?page_size=50    → taille de page personnalisée (100 maximum)

Format de réponse :
    {"count": 57, "next": "<url page suivante>", "previous": null, "results": [...]}
"""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def paginated_response(request, view, queryset, serializer_class, context=None, extra=None):
    """
    Découpe `queryset` selon les paramètres de la requête et renvoie la page demandée.
    `extra` permet d'ajouter des champs à la réponse (ex : un résumé).
    """
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request, view=view)
    serializer = serializer_class(page, many=True, context=context or {})
    response = paginator.get_paginated_response(serializer.data)
    if extra:
        response.data = {**extra, **response.data}
    return response
