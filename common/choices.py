"""
Listes de choix partagées entre plusieurs apps NOUNOU+.

Centralisées ici pour qu'un client et un travailleur parlent exactement
le même langage (ex : « temps plein ») sans import croisé entre apps.
"""

AVAILABILITY_FULL = "temps_plein"
AVAILABILITY_PART = "temps_partiel"
AVAILABILITY_WEEKEND = "weekends"

AVAILABILITY_CHOICES = [
    (AVAILABILITY_FULL, "Temps plein"),
    (AVAILABILITY_PART, "Temps partiel"),
    (AVAILABILITY_WEEKEND, "Weekends uniquement"),
]
