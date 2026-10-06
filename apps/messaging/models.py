"""
Modèle Message — messagerie interne entre un client et un travailleur.

Règles :
- On ne peut écrire et lire qu'à l'intérieur d'un match mutuel.
- Si l'une des parties revient sur le match, la conversation se ferme
  (l'historique n'est plus accessible tant que le match n'est pas de nouveau mutuel).
- Modération basique : l'administrateur peut retirer un message. Il reste
  visible dans la conversation sous la forme « message retiré par la modération ».
"""
from django.conf import settings
from django.db import models

MAX_MESSAGE_LENGTH = 2000


class Message(models.Model):
    match = models.ForeignKey(
        "matching.Match",
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Mise en relation",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="Expéditeur",
    )
    content = models.TextField(max_length=MAX_MESSAGE_LENGTH, verbose_name="Contenu")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")
    is_hidden = models.BooleanField(
        default=False,
        verbose_name="Retiré par la modération",
        help_text="Le contenu n'est plus montré aux participants.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.phone} → match #{self.match_id} : {self.content[:40]}"
