"""
Permissions de l'app workers.

Les classes sont désormais définies dans common/permissions.py.
Ce fichier les réexporte pour maintenir la compatibilité avec l'existant.
"""
from common.permissions import IsClient, IsWorker, IsWorkerOrClient  # noqa: F401
