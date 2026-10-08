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


VERIFIED_WORKER_ONLY_MESSAGE = (
    "Les familles et leurs annonces sont visibles une fois votre profil vérifié par l'équipe NOUNOU+."
)


class IsVerifiedWorker(IsWorker):
    """
    Travailleur dont le profil a été vérifié par l'équipe : seul autorisé à voir les
    familles et leurs annonces (prénom, quartier, budget, besoins).
    """

    message = VERIFIED_WORKER_ONLY_MESSAGE

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = getattr(request.user, "worker_profile", None)
        return profile is not None and profile.is_verified


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
