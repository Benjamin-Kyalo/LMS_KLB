"""Validation for administrator-uploaded public-site images.

The browser's content type is only a hint. A file is accepted when its name,
bytes and decoded image all agree, so a renamed script cannot become a hero
photo.
"""
import os

from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

HERO_IMAGE_MAX_BYTES = 5 * 1024 * 1024
HERO_IMAGE_MIN_SIZE = (640, 360)
HERO_IMAGE_FORMATS = {
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "WEBP": {".webp"},
}
HERO_IMAGE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp",
}


def validate_hero_image(upload):
    """Return a safe extension after checking size, bytes and dimensions."""
    if upload is None:
        raise ValidationError({"image": "Choose a photo to upload."})
    if upload.size > HERO_IMAGE_MAX_BYTES:
        raise ValidationError({"image": "The photo must be 5 MB or smaller."})

    extension = os.path.splitext(upload.name or "")[1].lower()
    if extension not in {ext for options in HERO_IMAGE_FORMATS.values() for ext in options}:
        raise ValidationError({"image": "Use a JPG, PNG or WebP photo."})

    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in HERO_IMAGE_CONTENT_TYPES:
        raise ValidationError({"image": "Use a JPG, PNG or WebP photo."})

    try:
        upload.seek(0)
        with Image.open(upload) as image:
            image_format = image.format
            width, height = image.size
            image.verify()
    except (
        Image.DecompressionBombError, UnidentifiedImageError, OSError,
        SyntaxError, ValueError,
    ):
        raise ValidationError({"image": "The file is not a readable image."}) from None
    finally:
        try:
            upload.seek(0)
        except (AttributeError, OSError, ValueError):
            pass

    if image_format not in HERO_IMAGE_FORMATS or extension not in HERO_IMAGE_FORMATS[image_format]:
        raise ValidationError({"image": "The photo bytes do not match its file name."})
    if width < HERO_IMAGE_MIN_SIZE[0] or height < HERO_IMAGE_MIN_SIZE[1]:
        raise ValidationError({
            "image": f"Use a photo at least {HERO_IMAGE_MIN_SIZE[0]}×{HERO_IMAGE_MIN_SIZE[1]} pixels.",
        })
    return extension


# Public name for the shared validator; the old name remains for callers and
# tests that predate the managed photo slots.
validate_site_image = validate_hero_image
