"""
Modèle Review — évaluation bidirectionnelle après la période d'essai.

Règles validées par le fondateur :
- Seules deux personnes ayant eu un match mutuel peuvent s'évaluer, une seule fois chacune.
- L'évaluation est possible à partir de 7 jours après le premier match mutuel.
- Notes de 1 à 5 :
    · un client note un travailleur sur : ponctualité, compétence, fiabilité ;
    · un travailleur note un client sur : respect, clarté des consignes, paiement à temps ;
  plus un commentaire facultatif.
- La moyenne et le nombre d'avis s'affichent sur le profil. Les commentaires sont
  visibles, l'auteur étant présenté par son prénom et l'initiale de son nom.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_COMMENT_LENGTH = 1000

# Critères notés selon la personne évaluée
WORKER_CRITERIA = ["punctuality", "competence", "reliability"]
CLIENT_CRITERIA = ["respect", "clarity", "payment_on_time"]


def _score_field(verbose_name):
    return models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=verbose_name,
    )


class Review(models.Model):
    match = models.ForeignKey(
        "matching.Match",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Mise en relation",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="Auteur",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="Personne évaluée",
    )

    # --- Critères quand un client évalue un travailleur ---
    punctuality = _score_field("Ponctualité")
    competence = _score_field("Compétence")
    reliability = _score_field("Fiabilité")

    # --- Critères quand un travailleur évalue un client ---
    respect = _score_field("Respect")
    clarity = _score_field("Clarté des consignes")
    payment_on_time = _score_field("Paiement à temps")

    overall = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name="Note globale",
        help_text="Moyenne des trois critères, calculée automatiquement.",
    )
    comment = models.TextField(
        blank=True, default="", max_length=MAX_COMMENT_LENGTH, verbose_name="Commentaire"
    )
    comment_hidden = models.BooleanField(
        default=False,
        verbose_name="Commentaire retiré par la modération",
        help_text="La note reste comptée, mais le commentaire n'est plus affiché.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["match", "author"], name="unique_review_per_match_author"),
        ]

    def __str__(self):
        return f"{self.author.phone} → {self.target.phone} : {self.overall}/5"

    @property
    def criteria(self) -> list[str]:
        """Les critères utilisés par cette évaluation."""
        return WORKER_CRITERIA if self.punctuality is not None else CLIENT_CRITERIA

    def compute_overall(self) -> Decimal:
        scores = [getattr(self, name) for name in self.criteria]
        average = Decimal(sum(scores)) / len(scores)
        return average.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.overall = self.compute_overall()
        super().save(*args, **kwargs)


def rating_summary(user) -> dict:
    """Moyenne et nombre d'avis reçus par un utilisateur (affichés sur son profil)."""
    stats = user.reviews_received.aggregate(average=models.Avg("overall"), count=models.Count("id"))
    average = stats["average"]
    return {
        "average": str(Decimal(average).quantize(Decimal("0.1"))) if average is not None else None,
        "count": stats["count"],
    }
