"""
Favoris : une famille met de côté des profils de travailleurs, un travailleur
met de côté des annonces. Personne n'est prévenu qu'il a été mis en favori.
"""
from django.conf import settings
from django.db import models


class FavoriteWorker(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_workers",
        verbose_name="Famille",
    )
    worker = models.ForeignKey(
        "workers.WorkerProfile",
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Travailleur",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ajouté le")

    class Meta:
        verbose_name = "Travailleur en favori"
        verbose_name_plural = "Travailleurs en favori"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "worker"], name="unique_favorite_worker")]


class FavoriteJob(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_jobs",
        verbose_name="Travailleur",
    )
    job = models.ForeignKey(
        "jobs.JobRequest",
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Annonce",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ajoutée le")

    class Meta:
        verbose_name = "Annonce en favori"
        verbose_name_plural = "Annonces en favori"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "job"], name="unique_favorite_job")]
