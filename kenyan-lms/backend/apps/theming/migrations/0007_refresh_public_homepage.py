# 27 November 2026: install the redesigned public homepage wording for sites
# that already saved a public content document. Custom edits are never replaced.

from copy import deepcopy

from django.db import migrations


OLD_HEADER_LINKS = [
    {"label": "Platform", "href": "/#workspaces"},
    {"label": "Library", "href": "/library"},
    {"label": "Who it's for", "href": "/#roles"},
]

NEW_HEADER_LINKS = [
    {"label": "Platform", "href": "/#workspaces"},
    {"label": "How it works", "href": "/#journey"},
    {"label": "Library", "href": "/library"},
    {"label": "Who it's for", "href": "/#roles"},
    {"label": "FAQ", "href": "/#faq"},
]

OLD_HERO_DESCRIPTION = (
    "A single KLB ecosystem for lessons, school records and digital textbooks, "
    "built for competency based learning."
)
NEW_HERO_DESCRIPTION = (
    "Courses, school records and digital textbooks now live in one calm "
    "workspace, designed for competency based learning and modest connections."
)

OLD_HERO_CAPTION = "One school record, with the right view for every role."
NEW_HERO_CAPTION = (
    "One school record, with the right view for every learner, teacher and guardian."
)

NEW_HERO_HIGHLIGHTS = [
    "Plan lessons and record progress",
    "Keep school records in one place",
    "Open digital books and resources",
]

NEW_SECTIONS = {
    "trust": {
        "overline": "Why schools choose KLB",
        "title": "Built for the way schools work",
        "items": [
            {
                "key": "connected",
                "title": "One connected record",
                "copy": (
                    "Courses, attendance, assessments and books share the same "
                    "school information."
                ),
            },
            {
                "key": "roles",
                "title": "The right view for every role",
                "copy": (
                    "Learners, guardians and teachers each see the tools and "
                    "records they need."
                ),
            },
            {
                "key": "modest",
                "title": "Useful on modest connections",
                "copy": (
                    "Simple pages and clear actions keep everyday school work moving."
                ),
            },
        ],
    },
    "journey": {
        "overline": "A simple first week",
        "title": "Start with three clear steps",
        "description": (
            "No technical setup is needed to explore the platform. Choose your "
            "path, open your workspace and build a routine that fits your school."
        ),
        "steps": [
            {
                "index": "01",
                "title": "Choose your path",
                "copy": (
                    "Compare the learner, guardian and teacher views before you sign in."
                ),
            },
            {
                "index": "02",
                "title": "Open your workspace",
                "copy": (
                    "Use the account issued by your school, or register where your "
                    "role allows it."
                ),
            },
            {
                "index": "03",
                "title": "Find what you need",
                "copy": (
                    "Move between courses, records and the digital library without "
                    "leaving the ecosystem."
                ),
            },
        ],
    },
    "spotlight": {
        "overline": "Digital library",
        "title": "Find the right resource faster",
        "description": (
            "Start with a title, a learning area or a collection. The public "
            "catalogue shows what is available before you sign in, while full "
            "textbook access stays with your school licence."
        ),
        "actionLabel": "Search the library",
        "actionHref": "/library",
        "imageSrc": "/images/hero-students.jpg",
        "imageAlt": "Students studying together with books and notebooks",
        "imageCaption": "Browse published titles and learning resources.",
    },
    "faq": {
        "overline": "Good to know",
        "title": "Questions people ask first",
        "description": (
            "Short answers about accounts, access and the way information is "
            "shared across the platform."
        ),
        "items": [
            {
                "question": "Do I need an invitation to register?",
                "answer": (
                    "Learner, guardian and teacher accounts start at the public "
                    "registration page. Teacher accounts wait for school approval, "
                    "while administrator accounts always use a secure invitation."
                ),
            },
            {
                "question": "Can a guardian follow more than one learner?",
                "answer": (
                    "Yes. The school links guardians to the right learners, and the "
                    "guardian workspace shows attendance, results and messages for "
                    "those links."
                ),
            },
            {
                "question": "What happens if a save does not work?",
                "answer": (
                    "This is a normal web app. A failed save stays unsaved, shows a "
                    "clear error and leaves the last saved information in place so "
                    "you can try again."
                ),
            },
            {
                "question": "Who can see a learner's records?",
                "answer": (
                    "Access follows the permissions set by the school. Learners see "
                    "their own records, guardians see linked learners and staff see "
                    "only the classes and tools their role allows."
                ),
            },
        ],
    },
}

NEW_FOOTER_FIELDS = {
    "tagline": "One calm place for lessons, school records and digital books.",
    "contactTitle": "Contact and help",
    "exploreTitle": "Explore",
    "exploreLinks": [
        {"label": "Platform", "href": "/#workspaces"},
        {"label": "How it works", "href": "/#journey"},
        {"label": "Public library", "href": "/library"},
    ],
    "learnTitle": "Learn more",
    "learnLinks": [
        {"label": "Role guide", "href": "/#roles"},
        {"label": "Common questions", "href": "/#faq"},
        {"label": "Progress insight", "href": "/#insights"},
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


def refresh_homepage(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        content = record.content or {}
        changed = False
        guarded = (
            ("header.links", OLD_HEADER_LINKS, NEW_HEADER_LINKS),
            ("hero.description", OLD_HERO_DESCRIPTION, NEW_HERO_DESCRIPTION),
            ("hero.imageCaption", OLD_HERO_CAPTION, NEW_HERO_CAPTION),
        )
        for path, previous, new in guarded:
            if _get(content, path) == previous:
                changed = _set(content, path, new) or changed
        for path, value in (
            ("hero.eyebrow", "Built for Kenyan classrooms"),
            ("hero.highlights", NEW_HERO_HIGHLIGHTS),
        ):
            if _get(content, path) is None:
                changed = _set(content, path, value) or changed
        for section, value in NEW_SECTIONS.items():
            if _get(content, section) is None:
                changed = _set(content, section, value) or changed
        for field, value in NEW_FOOTER_FIELDS.items():
            path = f"footer.{field}"
            if _get(content, path) is None:
                changed = _set(content, path, value) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


def restore_previous_homepage(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        content = record.content or {}
        changed = False
        guarded = (
            ("header.links", NEW_HEADER_LINKS, OLD_HEADER_LINKS),
            ("hero.description", NEW_HERO_DESCRIPTION, OLD_HERO_DESCRIPTION),
            ("hero.imageCaption", NEW_HERO_CAPTION, OLD_HERO_CAPTION),
        )
        for path, installed, previous in guarded:
            if _get(content, path) == installed:
                changed = _set(content, path, previous) or changed
        for path in (
            "hero.eyebrow",
            "hero.highlights",
            "footer.tagline",
            "footer.contactTitle",
            "footer.exploreTitle",
            "footer.exploreLinks",
            "footer.learnTitle",
            "footer.learnLinks",
            *NEW_SECTIONS.keys(),
        ):
            changed = _delete(content, path) or changed
        if changed:
            record.save(update_fields=["content", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("theming", "0006_seed_managed_photos"),
    ]

    operations = [
        migrations.RunPython(refresh_homepage, restore_previous_homepage),
    ]
