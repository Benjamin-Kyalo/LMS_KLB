"""Default public-site wording and validation for admin-managed overrides.

The object below is the server-side source of truth for the editable public
site. It mirrors the frontend fallback so the site still renders when the API
is temporarily unavailable. All wording is original. Reference sites informed
the topics, not the copy.
"""
from urllib.parse import urlparse

from rest_framework.exceptions import ValidationError

from apps.theming.contrast import HEX_COLOUR, MIN_TEXT_CONTRAST, contrast_ratio

PUBLIC_SITE_KEY = "public"

# Allowlisted, section-scoped appearance controls. Empty values inherit the
# active palette or the shipped section design. There is deliberately no raw
# CSS field: an administrator can change one section without affecting another.
STYLE_SECTION_KEYS = (
    "header",
    "footer",
    "hero",
    "workspaces",
    "workspace-learning",
    "workspace-school",
    "workspace-publishing",
    "insights",
    "roles",
    "library",
    "login",
    "register",
    "invite",
    "tutor",
)
STYLE_COLOUR_KEYS = ("background", "text", "accent", "border")
STYLE_CHOICES = {
    "radius": ("", "0px", "8px", "16px", "24px"),
    "spacing": ("", "compact", "comfortable", "relaxed"),
}
STYLE_FIELDS = STYLE_COLOUR_KEYS + tuple(STYLE_CHOICES)


def default_site_styles():
    """Return fresh per-section style controls with no overrides applied."""
    return {
        section: {field: "" for field in STYLE_FIELDS}
        for section in STYLE_SECTION_KEYS
    }


DEFAULT_SITE_CONTENT = {
    "header": {
        "brand": {
            "mark": "KLB",
            "name": "Digital Learning Ecosystem",
            "subtitle": "Kenya Literature Bureau",
        },
        "links": [
            {"label": "Platform", "href": "/#workspaces"},
            {"label": "Library", "href": "/library"},
            {"label": "Who it's for", "href": "/#roles"},
        ],
        "signInLabel": "Sign in",
        "signInHref": "/login",
        "authLinks": [{"label": "Sign in", "href": "/login"}],
        "adminLinks": [
            {"label": "Admin sign in", "href": "/admin/login"},
            {"label": "User registration", "href": "/register"},
        ],
    },
    "footer": {
        "name": "KLB Digital Learning Ecosystem",
        "lines": [
            "Kenya Literature Bureau, Nairobi, Kenya",
            "Access help: contact your school administrator",
            "Learning management, school information and digital publishing",
        ],
        "credit": {
            "prefix": "Photography via ",
            "linkLabel": "Unsplash",
            "linkHref": "https://unsplash.com/license",
            "suffix": " and illustration by KLB",
        },
    },
    "hero": {
        "overline": "One connected platform",
        "title": "Teaching and learning, connected for Kenyan schools.",
        "description": (
            "A single KLB ecosystem for lessons, school records and digital "
            "textbooks, built for competency based learning."
        ),
        "primaryLabel": "Create an account",
        "primaryHref": "/register",
        "secondaryLabel": "Browse the library",
        "secondaryHref": "/library",
        "imageSrc": "/images/hero-community.png",
        "imageAlt": "Students and teachers in a school learning space",
        "imageCaption": "One school record, with the right view for every role.",
    },
    "workspaces": {
        "overline": "What the platform does",
        "title": "Three connected ways to use KLB",
        "cards": [
            {
                "key": "learning",
                "label": "Learning workspace",
                "index": "01",
                "title": "Learning in one place",
                "copy": (
                    "Courses, assignments, quizzes and a textbook library "
                    "share the same school records."
                ),
                "image": "/images/workspace-skill.jpg",
                "imageAlt": "Learner practising a school skill",
            },
            {
                "key": "school",
                "label": "School day",
                "index": "02",
                "title": "Records that stay connected",
                "copy": (
                    "Attendance, timetables, assessments and class records "
                    "share one school database with the learner portal."
                ),
                "image": "/images/workspace-education.jpg",
                "imageAlt": "Education and school records in use",
            },
            {
                "key": "publishing",
                "label": "Digital publishing",
                "index": "03",
                "title": "Curriculum tied to the classroom",
                "copy": (
                    "Textbooks, chapters, resources and competency based "
                    "outcomes stay linked to the lessons teachers use."
                ),
                "image": "/images/digital-library.jpg",
                "imageAlt": "Library shelves holding reference books",
            },
        ],
    },
    "insights": {
        "overline": "Progress and insight",
        "title": "A clearer picture of learning",
        "description": (
            "School information is most useful when it is easy to read. The "
            "same records used for daily work also feed the dashboards and "
            "reports that teachers, managers and guardians rely on."
        ),
        "points": [
            {"title": "Attendance", "copy": "Daily registers stay linked to the class and learner record."},
            {"title": "Assessments", "copy": "Marks and feedback sit beside the courses they assess."},
            {"title": "Course activity", "copy": "Lessons, resources and submissions share one academic timeline."},
        ],
        "chip": "Attendance, assessments and courses",
        "caption": "Illustrative view of records already captured by the school.",
        "imageSrc": "/images/insight-success.jpg",
        "imageAlt": "A learner celebrating academic progress",
    },
    "roles": {
        "overline": "Choose your path",
        "title": "Where do you fit?",
        "description": (
            "Pick the area that sounds like you. We will show what you can "
            "open, what you can do and where to start."
        ),
        "previewLabel": "Access preview",
        "rightsTitle": "What you can do",
        "contentTitle": "What you will see",
        "cards": [
            {
                "key": "learners",
                "label": "Students & learners",
                "title": "Learn at your own pace",
                "copy": (
                    "Open your courses, assignments, quizzes and digital "
                    "books, all linked to your school record."
                ),
                "to": "/login?role=LEARNER",
                "action": "Learner workspace",
                "rights": [
                    "Work only inside your own learner record",
                    "Open your courses, assignments and quizzes",
                    "Track feedback and results in one place",
                    "Read your results, progress report and messages",
                ],
                "content": [
                    "My courses and textbook library",
                    "Assignments and quizzes",
                    "Learning resources",
                    "Progress report and school messages",
                ],
            },
            {
                "key": "guardians",
                "label": "Parents & guardians",
                "title": "Stay close to progress",
                "copy": (
                    "See attendance, results and school messages for the "
                    "learners linked to you, with clear updates that are "
                    "easy to follow."
                ),
                "to": "/login?role=GUARDIAN",
                "action": "Guardian workspace",
                "rights": [
                    "View progress for the learners linked to you",
                    "Read attendance, results and school messages",
                    "Update your own guardian profile",
                    "No staff or administration permissions",
                ],
                "content": [
                    "Linked learner progress",
                    "Attendance and assessment results",
                    "School messages",
                    "Guardian profile",
                ],
            },
            {
                "key": "teachers",
                "label": "Teachers",
                "title": "Plan, teach and assess",
                "copy": (
                    "Plan lessons, keep class records, mark work and use "
                    "curriculum tools in one calm workspace."
                ),
                "to": "/login?role=TEACHER",
                "action": "Teacher workspace",
                "rights": [
                    "Prepare courses, lessons, assignments and quizzes",
                    "Record attendance and manage class results",
                    "View learner records for your classes",
                    "No user administration or staff appointment permissions",
                ],
                "content": [
                    "Courses, modules and lessons",
                    "Assignments, submissions and question bank",
                    "Timetable, attendance and exams",
                    "Learners and curriculum tools",
                ],
            },
        ],
    },
    "library": {
        "overline": "Public library",
        "title": "Find books and learning resources",
        "description": (
            "Browse the KLB catalogue for published titles and learning "
            "resources. Open a book preview or filter resources by level, "
            "learning area, collection and keyword."
        ),
        "booksOverline": "Textbook catalogue",
        "booksTitle": "Books to explore",
        "booksDescription": (
            "See published titles from the catalogue. Full book access "
            "depends on your school licence and is managed by your "
            "administrator."
        ),
        "resourcesOverline": "Learning resources",
        "resourcesTitle": "Find learning resources",
        "resourcesDescription": (
            "Browse published resources by level, learning area, collection "
            "and keyword. Start with a textbook topic, a document or a "
            "curated collection."
        ),
    },
    "auth": {
        "login": {
            "publicHeading": "One platform for teaching, records and textbooks.",
            "adminHeading": "One administration portal for the whole school.",
            "storyCopy": (
                "Built for Kenyan schools with competency based learning, "
                "school administration and a digital publishing library. "
                "It works well on modest connections."
            ),
            "storyImageSrc": "/images/signin-time.jpg",
            "footnote": "Kenya Literature Bureau, Digital Education",
            "publicIntro": "Use the account your school administrator created, or register below.",
            "adminIntro": "Use an administrator account issued by your institution or platform administrator.",
        },
        "register": {
            "overline": "Create your account",
            "heading": "Choose your role, then fill in only what applies.",
            "copy": (
                "Learner and guardian accounts are ready to use straight "
                "away. Teacher accounts wait for approval by the school. "
                "Administrator accounts need a secure invitation and are "
                "never created through this form."
            ),
            "notice": "The school database is shared, so accounts created here appear in the administration portal for the same institution.",
            "storyImageSrc": "/images/register-learn.jpg",
            "steps": [
                "Choose account type",
                "Add your details",
                "Complete your role setup",
            ],
            "roleOptions": [
                {"value": "LEARNER", "label": "Learner", "note": "Courses, assignments and results"},
                {"value": "GUARDIAN", "label": "Parent / Guardian", "note": "Follow a learner's progress"},
                {"value": "TEACHER", "label": "Teacher", "note": "Created pending school approval"},
            ],
        },
        "admin": {
            "overline": "Administration portal",
            "heading": "Administrator accounts use invitations only.",
            "copy": (
                "A platform or school administrator must issue a secure, "
                "single use invitation token. The token fixes the role and "
                "school. This form cannot grant administrator privileges by "
                "itself. Each token works once and expires after seven days."
            ),
            "warning": (
                "Do not share invitation tokens or passwords over unsecured "
                "channels. If you do not have a token, contact your "
                "platform administrator."
            ),
        },
    },
    "portal": {
        "tutorImageSrc": "/images/tutor-brain.jpg",
        "tutorImageAlt": "A learner thinking through a problem",
    },
    "app": {
        "adminBrand": "KLB Learning",
        "portalBrand": "KLB Learning",
        "portalNav": [
            {"key": "home", "label": "Home"},
            {"key": "courses", "label": "My courses"},
            {"key": "textbooks", "label": "Textbook library"},
            {"key": "resources", "label": "Resources"},
            {"key": "documents", "label": "Documents"},
            {"key": "assignments", "label": "Assignments"},
            {"key": "quizzes", "label": "Quizzes"},
            {"key": "reports", "label": "Progress report"},
            {"key": "remediation", "label": "My support tasks"},
            {"key": "fees", "label": "Fees"},
            {"key": "tutor", "label": "Ask the tutor"},
            {"key": "communications", "label": "Messages"},
            {"key": "profile", "label": "My profile"},
        ],
    },
    "styles": default_site_styles(),
}


IMAGE_KEYS = {"image", "imageSrc", "storyImageSrc", "tutorImageSrc"}
LINK_KEYS = {
    "href", "linkHref", "primaryHref", "secondaryHref", "signInHref", "to",
} | IMAGE_KEYS
MAX_TEXT_LENGTH = 4000
MAX_LIST_LENGTH = 60
RETIRED_ROLE_KEYS = {"content"}
RETIRED_NAV_KEYS = {"sync"}
RETIRED_OFFLINE_COPY = {
    "Courses, assignments, quizzes and a textbook library in one place. "
    "Changes wait safely on the device and sync when the connection returns.": (
        "Courses, assignments, quizzes and a textbook library share the same "
        "school records."
    ),
    "Open your courses, assignments, quizzes and digital books. Your work "
    "waits safely on the device and syncs when you are back online.": (
        "Open your courses, assignments, quizzes and digital books, all linked "
        "to your school record."
    ),
    ". It is built for competency based learning and works when the network "
    "is not.": ", built for competency based learning.",
    "Lessons that continue offline": "Learning in one place",
    "Submit work while offline and sync on reconnect": "Track feedback and results in one place",
}


def _without_retired_role_cards(content):
    """Drop the retired content manager preview, even from old saved data."""
    if not isinstance(content, dict):
        return content
    roles = content.get("roles")
    cards = roles.get("cards") if isinstance(roles, dict) else None
    if not isinstance(cards, list):
        return content
    kept = [
        card for card in cards
        if isinstance(card, dict)
        and card.get("key") not in RETIRED_ROLE_KEYS
        and "content manager" not in str(card.get("label", "")).lower()
    ]
    if len(kept) == len(cards):
        return content
    updated = dict(content)
    updated["roles"] = {**roles, "cards": kept}
    return updated


def _without_retired_nav_items(content):
    """Drop the retired offline queue link, even from old saved data."""
    if not isinstance(content, dict):
        return content
    app = content.get("app")
    nav = app.get("portalNav") if isinstance(app, dict) else None
    if not isinstance(nav, list):
        return content
    kept = [
        item for item in nav
        if isinstance(item, dict) and item.get("key") not in RETIRED_NAV_KEYS
    ]
    if len(kept) == len(nav):
        return content
    updated = dict(content)
    updated["app"] = {**app, "portalNav": kept}
    return updated


def _replace_retired_offline_copy(value):
    """Replace known offline-era wording in saved edits as well as defaults."""
    if isinstance(value, str):
        for old, new in RETIRED_OFFLINE_COPY.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_replace_retired_offline_copy(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_retired_offline_copy(item)
            for key, item in value.items()
        }
    return value


def _strip_retired_content(content):
    content = _without_retired_nav_items(_without_retired_role_cards(content))
    return _replace_retired_offline_copy(content)


def default_site_content():
    """Return a fresh copy so callers never mutate the module constant."""
    return deep_merge(DEFAULT_SITE_CONTENT, {})


def deep_merge(template, overrides):
    """Copy the template, replacing only the keys present in overrides."""
    if isinstance(template, dict):
        result = {key: deep_merge(value, None) for key, value in template.items()}
        if isinstance(overrides, dict):
            for key, value in overrides.items():
                if key in template:
                    result[key] = deep_merge(template[key], value)
        return result
    if isinstance(template, list):
        if isinstance(overrides, list):
            return overrides
        return [deep_merge(item, None) for item in template]
    return overrides if isinstance(overrides, type(template)) else template


def _normalise_styles(value):
    """Validate section-scoped colours and layout choices."""
    if not isinstance(value, dict):
        raise ValidationError({"styles": "Section styles must be an object."})
    result = {}
    for section in STYLE_SECTION_KEYS:
        section_value = value.get(section, {})
        if not isinstance(section_value, dict):
            raise ValidationError({f"styles.{section}": "This section must be an object."})
        clean = {}
        for field in STYLE_COLOUR_KEYS:
            colour = section_value.get(field, "")
            if colour in ("", None):
                clean[field] = ""
            elif not isinstance(colour, str) or not HEX_COLOUR.fullmatch(colour):
                raise ValidationError({
                    f"styles.{section}.{field}": "Enter a six-digit hex colour such as #FFFFFF."
                })
            else:
                clean[field] = colour.upper()
        for field, choices in STYLE_CHOICES.items():
            choice = section_value.get(field, "")
            if choice not in choices:
                raise ValidationError({
                    f"styles.{section}.{field}": "Choose one of the supplied options."
                })
            clean[field] = choice
        background = clean["background"]
        text = clean["text"]
        if background and text and contrast_ratio(background, text) < MIN_TEXT_CONTRAST:
            raise ValidationError({
                f"styles.{section}.text": (
                    "This text colour has less than 4.5:1 contrast on the section "
                    "background. Choose a lighter or darker colour."
                )
            })
        result[section] = clean
    return result


def _safe_link(value, path):
    text = str(value or "")
    if text.startswith("/") and not text.startswith("//"):
        return text
    parsed = urlparse(text)
    if parsed.scheme == "https" and parsed.netloc:
        return text
    raise ValidationError({path: "Use a site path or a full HTTPS address."})


def _normalise(value, template, path):
    if isinstance(template, str):
        if not isinstance(value, str) or len(value) > MAX_TEXT_LENGTH:
            raise ValidationError({path: "Enter text of 4000 characters or fewer."})
        key = path.rsplit(".", 1)[-1]
        if key in IMAGE_KEYS and value == "":
            return ""
        return _safe_link(value, path) if key in LINK_KEYS else value
    if isinstance(template, dict):
        if not isinstance(value, dict):
            raise ValidationError({path: "This section must be an object."})
        result = {}
        for key, child_template in template.items():
            child_path = f"{path}.{key}" if path else key
            if key in value:
                result[key] = _normalise(value[key], child_template, child_path)
            else:
                result[key] = deep_merge(child_template, None)
        return result
    if isinstance(template, list):
        if not isinstance(value, list) or len(value) > MAX_LIST_LENGTH:
            raise ValidationError({path: f"Use a list of {MAX_LIST_LENGTH} items or fewer."})
        def item_path(index):
            return f"{path}.{index}" if path else str(index)

        if not template:
            return [_normalise(item, "", item_path(index)) for index, item in enumerate(value)]
        item_template = template[0]
        if isinstance(item_template, dict):
            result = []
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    raise ValidationError({path: f"Item {index + 1} must be an object."})
                result.append(_normalise(item, item_template, item_path(index)))
            return result
        return [
            _normalise(item, item_template, item_path(index))
            for index, item in enumerate(value)
        ]
    return value


def normalise_site_content(value):
    """Validate an admin edit and strip keys that are not in the schema."""
    if not isinstance(value, dict):
        raise ValidationError({"content": "Site content must be an object."})
    normalised = _normalise(value, DEFAULT_SITE_CONTENT, "")
    normalised["styles"] = _normalise_styles(normalised.get("styles", {}))
    return _strip_retired_content(normalised)


def public_site_content(overrides=None):
    """Merge stored overrides onto defaults for a safe public response."""
    merged = _strip_retired_content(deep_merge(DEFAULT_SITE_CONTENT, overrides or {}))
    try:
        merged["styles"] = _normalise_styles(merged.get("styles", {}))
    except ValidationError:
        # A stale saved value must never break the public page.
        merged["styles"] = default_site_styles()
    return merged
