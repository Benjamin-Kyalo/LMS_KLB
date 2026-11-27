# 27 November 2026: add the second set of public homepage features to sites
# that already saved a content document. Custom wording is never replaced.

from copy import deepcopy

from django.db import migrations


OLD_LEARN_LINKS = [
    {"label": "Role guide", "href": "/#roles"},
    {"label": "Common questions", "href": "/#faq"},
    {"label": "Progress insight", "href": "/#insights"},
]

NEW_LEARN_LINKS = [
    {"label": "Role guide", "href": "/#roles"},
    {"label": "Who sees what", "href": "/#access"},
    {"label": "Common questions", "href": "/#faq"},
    {"label": "Progress insight", "href": "/#insights"},
]

NEW_SECTIONS = {
    "announcement": {
        "text": "New this term: role previews make it easier to find your workspace.",
        "actionLabel": "See how it works",
        "actionHref": "/#journey",
    },
    "quickLinks": {
        "title": "On this page",
        "links": [
            {"label": "Workspaces", "href": "/#workspaces"},
            {"label": "Getting started", "href": "/#journey"},
            {"label": "Progress", "href": "/#insights"},
            {"label": "Library", "href": "/#spotlight"},
            {"label": "Roles", "href": "/#roles"},
            {"label": "Questions", "href": "/#faq"},
        ],
    },
    "routines": {
        "overline": "A day in the ecosystem",
        "title": "Small routines, one shared record",
        "description": (
            "The same information follows the school day, from planning a lesson "
            "to reviewing progress."
        ),
        "items": [
            {
                "key": "plan",
                "title": "Plan a lesson",
                "copy": "Teachers prepare courses, materials and assessments in one place.",
            },
            {
                "key": "record",
                "title": "Record the day",
                "copy": "Attendance, submissions and class notes stay linked to the learner.",
            },
            {
                "key": "review",
                "title": "Review progress",
                "copy": "Feedback, results and reports help the next lesson start with context.",
            },
        ],
    },
    "access": {
        "overline": "Clear boundaries",
        "title": "Who sees what",
        "description": (
            "Access follows the permissions set by the school. This short guide "
            "explains the everyday view for each role."
        ),
        "columns": ["Role", "Sees", "Can do"],
        "rows": [
            {
                "role": "Learners",
                "sees": "Their courses, work and results",
                "actions": "Submit work and read feedback",
            },
            {
                "role": "Guardians",
                "sees": "Linked learners' attendance and results",
                "actions": "Follow progress and read school messages",
            },
            {
                "role": "Teachers",
                "sees": "Their classes and curriculum tools",
                "actions": "Plan lessons, mark work and record attendance",
            },
        ],
    },
    "accessibility": {
        "overline": "Designed for everyone",
        "title": "Easy to use, by design",
        "items": [
            {
                "key": "keyboard",
                "title": "Keyboard friendly",
                "copy": "Every action has a visible focus and an accessible name.",
            },
            {
                "key": "motion",
                "title": "Motion you control",
                "copy": "Animations respect the reduced-motion setting.",
            },
            {
                "key": "bandwidth",
                "title": "Kind to connections",
                "copy": "Simple pages stay usable on modest bandwidth.",
            },
        ],
    },
    "support": {
        "overline": "Need a hand?",
        "title": "Help starts with your school",
        "description": (
            "Your school administrator can confirm accounts, permissions and "
            "access to digital books."
        ),
        "primaryLabel": "Read common questions",
        "primaryHref": "/#faq",
        "secondaryLabel": "See role access",
        "secondaryHref": "/#access",
    },
}

JOURNEY_FIELDS = {
    "checklistTitle": "Have these ready",
    "checklist": [
        "The role you are signing in as",
        "The account issued by your school",
        "A browser with a steady connection",
    ],
}


def _get(content, path):
    current = content
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set(content, path, value):
    parts = path.split(".")
    current = content
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return False
        current = current.setdefault(part, {})
    if not isinstance(current, dict):
        return False
    current[parts[-1]] = deepcopy(value)
    return True


def _delete(content, path):
    parts = path.split(".")
    current = content
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return False
        current = current.get(part)
    if isinstance(current, dict) and parts[-1] in current:
        del current[parts[-1]]
        return True
    return False


def add_homepage_extras(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        content = record.content or {}
        changed = False
        if _get(content, "footer.learnLinks") == OLD_LEARN_LINKS:
            changed = _set(content, "footer.learnLinks", NEW_LEARN_LINKS) or changed
        for section, value in NEW_SECTIONS.items():
            if _get(content, section) is None:
                changed = _set(content, section, value) or changed
        for field, value in JOURNEY_FIELDS.items():
            path = f"journey.{field}"
            if _get(content, path) is None:
                changed = _set(content, path, value) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


def remove_homepage_extras(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        content = record.content or {}
        changed = False
        if _get(content, "footer.learnLinks") == NEW_LEARN_LINKS:
            changed = _set(content, "footer.learnLinks", OLD_LEARN_LINKS) or changed
        for path in (
            *NEW_SECTIONS.keys(),
            "journey.checklistTitle",
            "journey.checklist",
        ):
            changed = _delete(content, path) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("theming", "0007_refresh_public_homepage"),
    ]

    operations = [
        migrations.RunPython(add_homepage_extras, remove_homepage_extras),
    ]
