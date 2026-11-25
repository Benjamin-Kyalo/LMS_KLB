# Generated for the approved managed-photo rollout on 25 November 2026.

from django.db import migrations

# (path, previous default or None, new default)
PHOTO_CHANGES = (
    ("hero.imageSrc", None, "/images/hero-community.png"),
    ("workspaces.cards.0.image", "/images/family-progress.jpg", "/images/workspace-skill.jpg"),
    (
        "workspaces.cards.0.imageAlt",
        "A parent and learner working together at a desk",
        "Learner practising a school skill",
    ),
    (
        "workspaces.cards.1.image",
        "/images/teachers-lesson.jpg",
        "/images/workspace-education.jpg",
    ),
    (
        "workspaces.cards.1.imageAlt",
        "A teacher working with students in a classroom",
        "Education and school records in use",
    ),
    ("insights.imageSrc", None, "/images/insight-success.jpg"),
    ("insights.imageAlt", None, "A learner celebrating academic progress"),
    ("auth.login.storyImageSrc", None, "/images/signin-time.jpg"),
    ("auth.register.storyImageSrc", None, "/images/register-learn.jpg"),
    ("portal.tutorImageSrc", None, "/images/tutor-brain.jpg"),
    ("portal.tutorImageAlt", None, "A learner thinking through a problem"),
)


def _parts(path):
    return [int(part) if part.isdigit() else part for part in path.split(".")]


def _parent(content, parts):
    current = content
    for part in parts[:-1]:
        if not isinstance(current, dict) and not isinstance(current, list):
            return None
        try:
            current = current[part]
        except (IndexError, KeyError, TypeError):
            return None
    return current if isinstance(current, (dict, list)) else None


def _get(content, path):
    parts = _parts(path)
    parent = _parent(content, parts)
    if parent is None:
        return None
    try:
        return parent[parts[-1]]
    except (IndexError, KeyError, TypeError):
        return None


def _set(content, path, value):
    parts = _parts(path)
    parent = _parent(content, parts)
    if parent is None:
        return False
    try:
        parent[parts[-1]] = value
    except (IndexError, KeyError, TypeError):
        return False
    return True


def _delete(content, path):
    parts = _parts(path)
    parent = _parent(content, parts)
    if parent is None:
        return False
    try:
        del parent[parts[-1]]
    except (IndexError, KeyError, TypeError):
        return False
    return True


def apply_photo_changes(apps, changes):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        changed = False
        for path, previous, new in changes:
            # A custom administrator photo is never overwritten. Only the old
            # default or a missing managed field receives the supplied photo.
            if _get(record.content, path) not in (None, previous):
                continue
            if previous is None:
                changed = _set(record.content, path, new) or changed
            else:
                changed = _set(record.content, path, new) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


def seed_managed_photos(apps, schema_editor):
    apply_photo_changes(apps, PHOTO_CHANGES)


def restore_previous_photos(apps, schema_editor):
    reverse = []
    for path, previous, new in PHOTO_CHANGES:
        reverse.append((path, new, previous))
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        changed = False
        for path, installed, previous in reverse:
            if _get(record.content, path) != installed:
                continue
            if previous is None:
                changed = _delete(record.content, path) or changed
            else:
                changed = _set(record.content, path, previous) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("theming", "0005_set_shared_hero_photo"),
    ]

    operations = [
        migrations.RunPython(seed_managed_photos, restore_previous_photos),
    ]
