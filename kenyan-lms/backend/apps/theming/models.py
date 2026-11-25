"""Persistent theme palette catalogue with exactly one active palette."""
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.theming.contrast import HEX_COLOUR
from apps.theming.site_content import default_site_content

SHADE_STEPS = (900, 800, 700, 600, 500, 400, 300, 200, 100)

hex_validator = RegexValidator(
    regex=HEX_COLOUR,
    message="Enter a six-digit hex colour such as #023E8A.",
)


class ThemePalette(TimeStampedModel):
    """A complete, reusable set of nine ramp colours.

    Components read semantic CSS variables derived from these shades. Adding a
    palette here therefore changes the whole application without code edits.
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    description = models.TextField(blank=True)
    source_label = models.CharField(
        max_length=160, blank=True,
        help_text="Where these colours came from, for example a design image name.",
    )
    shade_900 = models.CharField(max_length=7, validators=[hex_validator])
    shade_800 = models.CharField(max_length=7, validators=[hex_validator])
    shade_700 = models.CharField(max_length=7, validators=[hex_validator])
    shade_600 = models.CharField(max_length=7, validators=[hex_validator])
    shade_500 = models.CharField(max_length=7, validators=[hex_validator])
    shade_400 = models.CharField(max_length=7, validators=[hex_validator])
    shade_300 = models.CharField(max_length=7, validators=[hex_validator])
    shade_200 = models.CharField(max_length=7, validators=[hex_validator])
    shade_100 = models.CharField(max_length=7, validators=[hex_validator])
    is_active = models.BooleanField(default=False, db_index=True)
    is_builtin = models.BooleanField(default=False, editable=False)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_theme_palettes", editable=False,
    )

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True),
                name="only_one_active_theme_palette",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "palette"
            candidate = base
            suffix = 2
            while ThemePalette.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        return super().save(*args, **kwargs)

    @property
    def shades(self):
        """A numeric-key map matching the frontend theme contract."""
        return {step: getattr(self, f"shade_{step}") for step in SHADE_STEPS}


class SiteContent(TimeStampedModel):
    """One editable document for public wording, navigation and footer copy."""

    key = models.CharField(max_length=40, unique=True, editable=False)
    content = models.JSONField(default=default_site_content)
    updated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="updated_site_content", editable=False,
    )

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return "Public site content"
