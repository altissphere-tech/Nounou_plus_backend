"""
Règles de confidentialité partagées : ce qui est masqué avant un match mutuel.

Rappel du brief : le téléphone et le nom complet ne sont jamais exposés
à un autre utilisateur tant que le match n'est pas mutuel.
"""


def mask_last_name(last_name: str) -> str:
    """Réduit un nom de famille à son initiale. Ex : "Mutombo" → "M."."""
    last_name = (last_name or "").strip()
    return f"{last_name[0].upper()}." if last_name else ""
