"""
Photos de profil.

Règles validées par le fondateur :
- la photo est visible par tous (même avant un match), mais seulement après
  validation par l'équipe NOUNOU+ ;
- tant qu'elle n'est pas validée, seule la personne elle-même la voit.

À l'envoi, l'image est vérifiée, réduite (800 px maximum) et réenregistrée en JPEG :
les informations cachées du fichier (position GPS, appareil…) sont ainsi supprimées.
Le nom du fichier est aléatoire : l'adresse d'une photo ne peut pas être devinée.
"""
import uuid
import warnings
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_MB = 5
MAX_SIDE_PX = 800
# Au-delà (ex : image piégée, toute petite sur le disque mais énorme une fois ouverte),
# refus sans décompresser. 16 millions de pixels couvrent toutes les photos de téléphone.
MAX_PIXELS = 16_000_000
ACCEPTED_FORMATS = ("JPEG", "PNG", "WEBP")


class InvalidPhoto(ValueError):
    pass


def prepare_photo(uploaded) -> ContentFile:
    """Vérifie et nettoie l'image envoyée. Lève InvalidPhoto si ce n'est pas une image valide."""
    if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise InvalidPhoto(f"La photo dépasse {MAX_UPLOAD_MB} Mo.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            # Seuls ces formats sont lus : aucun autre décodeur d'images n'est sollicité
            image = Image.open(uploaded, formats=ACCEPTED_FORMATS)
            if image.width * image.height > MAX_PIXELS:
                raise InvalidPhoto("Cette image est trop grande.")
            if image.format == "JPEG":
                image.draft("RGB", (MAX_SIDE_PX * 2, MAX_SIDE_PX * 2))  # décode directement en plus petit
            image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise InvalidPhoto("Ce fichier n'est pas une image valide (JPG ou PNG).")
    if image.format not in ACCEPTED_FORMATS:
        raise InvalidPhoto("Formats acceptés : JPG, PNG ou WEBP.")
    image = ImageOps.exif_transpose(image)  # remet la photo à l'endroit
    image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))
    if image.mode != "RGB":
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
        image = background
    output = BytesIO()
    image.save(output, format="JPEG", quality=85)  # sans les métadonnées d'origine
    return ContentFile(output.getvalue(), name=f"{uuid.uuid4().hex}.jpg")


def set_photo(user, uploaded) -> None:
    """Remplace la photo de l'utilisateur ; elle repasse en attente de validation."""
    content = prepare_photo(uploaded)
    remove_photo_file(user)
    user.photo.save(content.name, content, save=False)
    user.photo_status = user.PHOTO_PENDING
    user.photo_rejection_reason = ""
    user.save(update_fields=["photo", "photo_status", "photo_rejection_reason"])


def remove_photo_file(user) -> None:
    if user.photo:
        user.photo.delete(save=False)


def delete_photo(user) -> None:
    remove_photo_file(user)
    user.photo = ""
    user.photo_status = user.PHOTO_NONE
    user.photo_rejection_reason = ""
    user.save(update_fields=["photo", "photo_status", "photo_rejection_reason"])


def review_photo(user, approved: bool, reason: str = "") -> None:
    """Décision de l'équipe. Une photo refusée est supprimée du disque."""
    from apps.notifications.models import notify

    if approved:
        user.photo_status = user.PHOTO_APPROVED
        user.photo_rejection_reason = ""
        user.save(update_fields=["photo_status", "photo_rejection_reason"])
    else:
        remove_photo_file(user)
        user.photo = ""
        user.photo_status = user.PHOTO_REJECTED
        user.photo_rejection_reason = reason or "Photo non conforme (visage peu visible ou image inappropriée)."
        user.save(update_fields=["photo", "photo_status", "photo_rejection_reason"])
    notify(user, "photo_reviewed", approved=approved, reason=user.photo_rejection_reason)


def public_photo_url(user) -> str | None:
    """Adresse de la photo pour les autres utilisateurs (None si absente ou non validée)."""
    if user.photo and user.photo_status == user.PHOTO_APPROVED:
        return f"/api/photos/{user.photo.name.rsplit('/', 1)[-1]}"
    return None
