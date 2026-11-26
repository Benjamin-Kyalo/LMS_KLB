"""Validation for administrator-managed palettes."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.theming.contrast import (
    HEX_COLOUR, MIN_TEXT_CONTRAST, contrast_ratio,
)
from apps.theming.models import SHADE_STEPS, SiteContent, ThemePalette
from apps.theming.site_content import normalise_site_content

TEXT_SHADE_STEPS = (900, 800, 700)


class ThemePaletteSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    shades = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True, allow_null=True,
    )

    class Meta:
        model = ThemePalette
        fields = [
            "id", "name", "slug", "description", "source_label",
            "shade_900", "shade_800", "shade_700", "shade_600", "shade_500",
            "shade_400", "shade_300", "shade_200", "shade_100", "shades",
            "is_active", "is_builtin", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "shades", "is_active", "is_builtin",
            "created_by_name", "created_at", "updated_at",
        ]

    def get_shades(self, obj):
        return obj.shades

    def validate(self, attrs):
        values = {}
        for step in SHADE_STEPS:
            field = f"shade_{step}"
            value = attrs.get(field)
            if value is None and self.instance is not None:
                value = getattr(self.instance, field)
            if not HEX_COLOUR.fullmatch(str(value or "")):
                raise serializers.ValidationError({
                    field: "Enter a six-digit hex colour such as #023E8A."
                })
            values[step] = value.upper()
            attrs[field] = values[step]

        for step in TEXT_SHADE_STEPS:
            ratio = contrast_ratio(values[step], "#FFFFFF")
            if ratio < MIN_TEXT_CONTRAST:
                raise serializers.ValidationError({
                    f"shade_{step}": (
                        f"This shade has only {ratio:.2f}:1 contrast on white. "
                        "Text shades must reach 4.5:1."
                    )
                })
        return attrs


class SiteContentSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    updated_by_name = serializers.CharField(
        source="updated_by.full_name", read_only=True, allow_null=True,
    )

    class Meta:
        model = SiteContent
        fields = ["id", "key", "content", "updated_by_name", "created_at", "updated_at"]
        read_only_fields = ["id", "key", "updated_by_name", "created_at", "updated_at"]

    def validate_content(self, value):
        return normalise_site_content(value)
