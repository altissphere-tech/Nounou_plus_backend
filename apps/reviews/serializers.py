"""
Serializers de l'app reviews.
"""
from rest_framework import serializers

from apps.accounts.models import User
from common.privacy import mask_last_name

from .models import CLIENT_CRITERIA, MAX_COMMENT_LENGTH, WORKER_CRITERIA, Review

HIDDEN_COMMENT = "Ce commentaire a été retiré par la modération."


class ReviewCreateSerializer(serializers.Serializer):
    """
    Création d'une évaluation. Les critères attendus dépendent de la personne évaluée
    (le contexte doit contenir `target_is_worker`).
    """

    punctuality = serializers.IntegerField(min_value=1, max_value=5, required=False)
    competence = serializers.IntegerField(min_value=1, max_value=5, required=False)
    reliability = serializers.IntegerField(min_value=1, max_value=5, required=False)
    respect = serializers.IntegerField(min_value=1, max_value=5, required=False)
    clarity = serializers.IntegerField(min_value=1, max_value=5, required=False)
    payment_on_time = serializers.IntegerField(min_value=1, max_value=5, required=False)
    comment = serializers.CharField(
        max_length=MAX_COMMENT_LENGTH, required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        expected = WORKER_CRITERIA if self.context["target_is_worker"] else CLIENT_CRITERIA
        other = CLIENT_CRITERIA if self.context["target_is_worker"] else WORKER_CRITERIA
        errors = {name: "Note de 1 à 5 obligatoire." for name in expected if name not in attrs}
        errors.update(
            {name: "Ce critère ne s'applique pas à cette évaluation." for name in other if name in attrs}
        )
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    """Une évaluation telle qu'affichée publiquement."""

    author_name = serializers.SerializerMethodField(
        help_text="Prénom et initiale du nom de l'auteur (ex : « Jean I. »)."
    )
    scores = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "author_name", "scores", "overall", "comment", "created_at"]
        read_only_fields = fields

    def get_author_name(self, obj) -> str:
        author = obj.author
        attr = "client_profile" if author.role == User.ROLE_CLIENT else "worker_profile"
        profile = getattr(author, attr, None)
        if profile is None:
            return "Utilisateur NOUNOU+"
        return f"{profile.first_name} {mask_last_name(profile.last_name)}".strip()

    def get_scores(self, obj) -> dict:
        return {name: getattr(obj, name) for name in obj.criteria}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.comment_hidden:
            data["comment"] = HIDDEN_COMMENT
        return data
