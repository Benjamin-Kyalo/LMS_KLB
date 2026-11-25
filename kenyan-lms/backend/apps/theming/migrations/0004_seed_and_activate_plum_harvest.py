# Generated for the approved Plum Harvest palette supplied on 25 November 2026.

from django.db import migrations

from apps.theming.catalogue import PLUM_HARVEST


def seed_and_activate_plum_harvest(apps, schema_editor):
    """Add the new built-in palette, then make it the single active palette."""
    ThemePalette = apps.get_model("theming", "ThemePalette")
    fields = {
        "name": PLUM_HARVEST["name"],
        "description": PLUM_HARVEST["description"],
        "source_label": PLUM_HARVEST["source_label"],
        "is_builtin": True,
    }
    fields.update({
        f"shade_{step}": colour
        for step, colour in PLUM_HARVEST["shades"].items()
    })
    record, _ = ThemePalette.objects.get_or_create(
        slug=PLUM_HARVEST["slug"],
        defaults={**fields, "is_active": False},
    )
    changed = False
    for field, value in fields.items():
        if getattr(record, field) != value:
            setattr(record, field, value)
            changed = True
    if changed:
        record.save()

    # Clear first: the database enforces exactly one active palette.
    ThemePalette.objects.exclude(pk=record.pk).filter(is_active=True).update(
        is_active=False
    )
    if not record.is_active:
        record.is_active = True
        record.save(update_fields=["is_active", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("theming", "0003_seed_swatch_palettes"),
    ]

    operations = [
        migrations.RunPython(seed_and_activate_plum_harvest, migrations.RunPython.noop),
    ]
