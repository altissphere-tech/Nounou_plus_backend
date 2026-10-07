"""
Vérification des adresses e-mail.

Une adresse n'est « vérifiée » qu'après un clic sur le lien reçu (ou si Google /
Apple la confirment). Seule une adresse vérifiée permet :
- de recevoir un lien « mot de passe oublié » ;
- de relier automatiquement un compte Google / Apple au compte existant.
Sans cela, quelqu'un pourrait s'inscrire avec l'adresse d'une autre personne et
récupérer ensuite son compte (prise de contrôle).

Une adresse non vérifiée ne « bloque » personne : si une autre personne l'utilise
et la vérifie (ou se connecte avec Google), elle lui est attribuée.
"""
import logging

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail

from .models import User

logger = logging.getLogger("nounou.security")

SALT = "nounou.email-verification"
MAX_AGE_SECONDS = 3 * 24 * 3600  # le lien est valable 3 jours


def release_unverified(email: str, keep: User | None = None) -> None:
    """Retire une adresse non vérifiée des autres comptes qui l'auraient saisie."""
    others = User.objects.filter(email=email, email_verified=False)
    if keep is not None:
        others = others.exclude(pk=keep.pk)
    others.update(email=None)


def set_email(user: User, email: str, verified: bool = False) -> None:
    """Enregistre l'adresse du compte. Non vérifiée : un lien de confirmation est envoyé."""
    email = email.strip().lower()
    release_unverified(email, keep=user)
    user.email = email
    user.email_verified = verified
    user.save(update_fields=["email", "email_verified"])
    if not verified:
        send_verification(user)


def send_verification(user: User) -> None:
    token = signing.dumps({"u": user.pk, "e": user.email}, salt=SALT)
    link = f"{settings.FRONTEND_URL}/email/confirmer?token={token}"
    send_mail(
        subject="NOUNOU+ — confirmez votre adresse e-mail",
        message=(
            "Bonjour,\n\nPour confirmer votre adresse e-mail sur NOUNOU+, ouvrez ce lien "
            f"(valable 3 jours) :\n{link}\n\n"
            "Si vous n'avez pas créé de compte NOUNOU+, ignorez simplement cet e-mail.\n\nL'équipe NOUNOU+"
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def confirm(token: str) -> User | None:
    """Valide le lien. Renvoie le compte confirmé, ou None si le lien est invalide ou périmé."""
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
    except signing.BadSignature:
        return None
    user = User.objects.filter(pk=data.get("u"), is_active=True).first()
    if user is None or user.email != data.get("e"):
        return None  # l'adresse a changé depuis l'envoi du lien
    if not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        logger.info("email_verified user=%s", user.pk)
    return user
