"""
Vérification des adresses e-mail.

Une adresse saisie reste « en attente » (`pending_email`) jusqu'au clic sur le lien
reçu. Tant qu'elle est en attente, elle ne sert à rien (ni connexion, ni « mot de
passe oublié », ni liaison Google / Apple) et elle ne retire rien à personne :
quelqu'un qui saisit l'adresse d'une autre personne ne peut pas la lui prendre.

Au clic sur le lien, l'adresse devient celle du compte (`email`, vérifiée) et
disparaît des autres comptes où elle était seulement en attente.
"""
from django.conf import settings
from django.core import signing
from django.core.mail import send_mail

from common.security_log import event

from .models import User

SALT = "nounou.email-verification"
MAX_AGE_SECONDS = 3 * 24 * 3600  # le lien est valable 3 jours


def _taken_by_other(email: str, user: User) -> bool:
    return User.objects.filter(email=email).exclude(pk=user.pk).exists()


def set_verified_email(user: User, email: str) -> None:
    """Adresse confirmée par Google / Apple : enregistrée directement, si elle est libre."""
    email = email.strip().lower()
    if user.email == email or _taken_by_other(email, user):
        return
    User.objects.filter(pending_email=email).exclude(pk=user.pk).update(pending_email="")
    user.email = email
    user.email_verified = True
    if user.pending_email == email:
        user.pending_email = ""
    user.save(update_fields=["email", "email_verified", "pending_email"])


def request_email(user: User, email: str) -> None:
    """
    Nouvelle adresse saisie par la personne : mise en attente, lien de confirmation envoyé.
    Si l'adresse appartient déjà à un autre compte, rien n'est changé : son titulaire est
    simplement prévenu (la réponse à l'utilisateur reste la même, sans indice).
    """
    email = email.strip().lower()
    if email == user.email:
        return
    if _taken_by_other(email, user):
        send_mail(
            subject="NOUNOU+ — votre adresse e-mail",
            message=(
                "Bonjour,\n\nQuelqu'un a essayé d'utiliser cette adresse e-mail sur un autre compte "
                "NOUNOU+. Elle reste liée à votre compte : vous n'avez rien à faire.\n\n"
                "Si vous avez oublié votre mot de passe, utilisez « Mot de passe oublié ».\n\nL'équipe NOUNOU+"
            ),
            from_email=None,
            recipient_list=[email],
        )
        return
    user.pending_email = email
    user.save(update_fields=["pending_email"])
    send_verification(user)


def send_verification(user: User) -> None:
    token = signing.dumps({"u": user.pk, "e": user.pending_email}, salt=SALT)
    link = f"{settings.FRONTEND_URL}/email/confirmer?token={token}"
    send_mail(
        subject="NOUNOU+ — confirmez votre adresse e-mail",
        message=(
            "Bonjour,\n\nPour confirmer votre adresse e-mail sur NOUNOU+, ouvrez ce lien "
            f"(valable 3 jours) :\n{link}\n\n"
            "Si vous n'avez pas créé de compte NOUNOU+, ignorez simplement cet e-mail.\n\nL'équipe NOUNOU+"
        ),
        from_email=None,
        recipient_list=[user.pending_email],
    )


def confirm(token: str) -> User | None:
    """Valide le lien. Renvoie le compte confirmé, ou None si le lien est invalide ou périmé."""
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
    except signing.BadSignature:
        return None
    user = User.objects.filter(pk=data.get("u"), is_active=True).first()
    if user is None:
        return None
    email = data.get("e")
    if user.email == email:
        return user  # lien déjà utilisé
    if not email or user.pending_email != email or _taken_by_other(email, user):
        return None  # l'adresse a changé depuis l'envoi du lien, ou a été prise entre-temps
    User.objects.filter(pending_email=email).exclude(pk=user.pk).update(pending_email="")
    user.email = email
    user.email_verified = True
    user.pending_email = ""
    user.save(update_fields=["email", "email_verified", "pending_email"])
    event("email_confirme", compte=user.pk)
    return user
