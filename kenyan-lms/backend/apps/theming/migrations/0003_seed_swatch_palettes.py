# Generated for the five palettes supplied on 25 November 2026.

from django.db import migrations

from apps.theming.catalogue import SWATCH_PALETTES


def seed_swatch_palettes(apps, schema_editor):
    """Add the supplied swatch palettes without changing the active choice."""
    ThemePalette = apps.get_model("theming", "ThemePalette")
    for palette in SWATCH_PALETTES:
        fields = {
            "name": palette["name"],
            "description": palette["description"],
            "source_label": palette["source_label"],
            "is_builtin": True,
        }
        fields.update({
            f"shade_{step}": colour
            for step, colour in palette["shades"].items()
        })
        record, created = ThemePalette.objects.get_or_create(
            slug=palette["slug"],
            defaults={**fields, "is_active": False},
        )
        if created:
            continue
        for field, value in fields.items():
            setattr(record, field, value)
        record.save()


class Migration(migrations.Migration):

    dependencies = [
        ("theming", "0002_sitecontent"),
    ]

    operations = [
        migrations.RunPython(seed_swatch_palettes, migrations.RunPython.noop),
    ]
