# Generated for the approved shared homepage/sign-in photo on 25 November 2026.

from django.db import migrations

OLD_IMAGE_SRC = "/images/hero-students.jpg"
NEW_IMAGE_SRC = "/images/hero-community.png"
OLD_IMAGE_ALT = "Students studying together with laptops and notebooks"
NEW_IMAGE_ALT = "Students and teachers in a school learning space"


def _set_photo(apps, from_src, to_src, from_alt, to_alt):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        hero = record.content.get("hero")
        if not isinstance(hero, dict):
            continue
        changed = False
        # Saved content may store only overrides. An absent imageSrc still needs
        # the new default; a custom uploaded path is left untouched.
        if hero.get("imageSrc") in (None, from_src):
            hero["imageSrc"] = to_src
            changed = True
        if hero.get("imageAlt") == from_alt:
            hero["imageAlt"] = to_alt
            changed = True
        if changed:
            record.save(update_fields=["content", "updated_at"])


def set_shared_hero_photo(apps, schema_editor):
    """Move the old default to the supplied shared photo without touching uploads."""
    _set_photo(apps, OLD_IMAGE_SRC, NEW_IMAGE_SRC, OLD_IMAGE_ALT, NEW_IMAGE_ALT)


def restore_previous_hero_photo(apps, schema_editor):
    _set_photo(apps, NEW_IMAGE_SRC, OLD_IMAGE_SRC, NEW_IMAGE_ALT, OLD_IMAGE_ALT)


class Migration(migrations.Migration):
    dependencies = [
        ("theming", "0004_seed_and_activate_plum_harvest"),
    ]

    operations = [
        migrations.RunPython(set_shared_hero_photo, restore_previous_hero_photo),
    ]
