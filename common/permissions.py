"""
Permissions partagées entre toutes les apps NOUNOU+.

Centralisées ici pour éviter les imports croisés entre apps
(ex : une app jobs qui importerait depuis une app workers — mauvaise pratique).
"""
from rest_framework.permissions import BasePermission
from apps.accounts.models import User


class IsWorker(BasePermission):
    """Autorise uniquement les utilisateurs ayant le rôle 'travailleur'."""

    message = "Seuls les travailleurs peuvent effectuer cette action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.ROLE_WORKER
        )


class IsClient(BasePermission):
    """Autorise uniquement les utilisateurs ayant le rôle 'client'."""

    message = "Seuls les clients peuvent effectuer cette action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.ROLE_CLIENT
        )


class IsWorkerOrClient(BasePermission):
    """Autorise les travailleurs ET les clients (tout utilisateur authentifié non-admin)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.ROLE_WORKER, User.ROLE_CLIENT)
        )
