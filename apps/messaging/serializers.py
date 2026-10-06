"""
Serializers de l'app messaging.
"""
from rest_framework import serializers

from .models import MAX_MESSAGE_LENGTH, Message

HIDDEN_CONTENT = "Ce message a été retiré par la modération."


class MessageSerializer(serializers.ModelSerializer):
    """
    Un message vu par un participant (le contexte doit contenir `request`).
    `is_mine` indique si l'utilisateur connecté en est l'expéditeur.
    """

    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "content", "is_mine", "is_hidden", "read_at", "created_at"]
        read_only_fields = fields

    def get_is_mine(self, obj) -> bool:
        return obj.sender_id == self.context["request"].user.id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_hidden:
            data["content"] = HIDDEN_CONTENT
        return data


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(
        max_length=MAX_MESSAGE_LENGTH,
        trim_whitespace=True,
        help_text=f"Texte du message ({MAX_MESSAGE_LENGTH} caractères maximum).",
    )
