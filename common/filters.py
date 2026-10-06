"""
Lecture des filtres de recherche passés dans l'URL (ex : ?max_salary=200&service=nounou).

Une valeur invalide renvoie une erreur 400 claire plutôt que d'être ignorée en silence.
"""
from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError


def get_decimal(request, name):
    """Retourne le paramètre `name` en nombre décimal positif, ou None s'il est absent."""
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValidationError({name: "Doit être un nombre (ex : 150 ou 150.50)."})
    if value < 0 or not value.is_finite():
        raise ValidationError({name: "Doit être un nombre positif."})
    return value


def get_int(request, name):
    """Retourne le paramètre `name` en entier positif, ou None s'il est absent."""
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError({name: "Doit être un nombre entier."})
    if value < 0:
        raise ValidationError({name: "Doit être un nombre positif."})
    return value


def get_choice(request, name, choices):
    """Retourne le paramètre `name` s'il fait partie des valeurs autorisées, sinon une erreur 400."""
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    allowed = [value for value, _label in choices]
    if raw not in allowed:
        raise ValidationError({name: f"Valeurs acceptées : {', '.join(allowed)}."})
    return raw


def get_text(request, name):
    """Retourne le paramètre texte `name` sans espaces superflus, ou None s'il est vide."""
    raw = (request.query_params.get(name) or "").strip()
    return raw or None
