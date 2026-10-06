"""
Catalogue des services proposés par les travailleurs NOUNOU+.

Pourquoi un modèle séparé ?
- Permet de filtrer les travailleurs par service avec l'ORM Django (filter(services__slug='nounou')).
- Extensible : ajouter un nouveau service ne nécessite qu'une entrée en base, pas de changement de code.
- Remplace le CharField CSV qui rendait les filtres impossibles.
"""
from django.db import models


class Service(models.Model):
    """
    Un type de service proposé par les travailleurs.

    Les 3 services initiaux (nounou, ménage, cuisine) sont insérés
    automatiquement via la migration 0001_initial.
    """

    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Identifiant",
        help_text="Identifiant court utilisé dans l'API (ex : 'nounou').",
    )
    label = models.CharField(
        max_length=100,
        verbose_name="Intitulé",
        help_text="Nom affiché dans l'interface (ex : 'Garde d'enfants').",
    )

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["slug"]

    def __str__(self):
        return self.label
