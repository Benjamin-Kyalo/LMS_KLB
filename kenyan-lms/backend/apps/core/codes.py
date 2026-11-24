"""Central, concurrency-safe generation of business reference numbers.

Every school-visible identifier (admission number, staff number, course code,
....) is allocated here so the format is consistent and two simultaneous
requests cannot receive the same value.

We use a PostgreSQL transaction-scoped advisory lock keyed by the model,
field and owner (institution or parent record). The lock is released
automatically when the surrounding transaction commits. No extra database
table or migration is required.
"""
import re

from django.apps import apps
from django.db import connection, transaction
from django.db.models import Max

STOP_WORDS = {"the", "of", "and", "for", "secondary", "primary", "school", "academy"}
GENERIC_ENDINGS = {"school", "academy", "college", "university", "institute"}

TRAILING_NUMBER = re.compile(r"-(\d+)$")
ALLOWED = re.compile(r"[^A-Z0-9]+")


def _lock(namespace, key):
    """Serialise code allocation for one logical owner."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s), hashtext(%s))",
            [namespace, key],
        )


def _token(value, fallback="SCH"):
    clean = ALLOWED.sub("", str(value or "").upper())
    return (clean[:10] or fallback)


def school_abbreviation(name):
    """Turn 'Kisumu Secondary School' into a short readable token like KSCH."""
    words = [w for w in re.findall(r"[A-Za-z0-9]+", str(name or ""))]
    if not words:
        return "SCH"
    meaningful = [w for w in words if w.lower() not in STOP_WORDS]
    if not meaningful:
        return _token(words[0][:4], "SCH")

    letters = "".join(word[0] for word in meaningful[:6])
    last = words[-1].lower()
    if last in GENERIC_ENDINGS and len(words[-1]) >= 3:
        candidate = letters + words[-1][:3]
    elif len(meaningful) > 1:
        candidate = letters
    else:
        candidate = meaningful[0][:5]
    return _token(candidate, "SCH")


def _highest_number(values, head):
    highest = 0
    for value in values:
        value = value or ""
        if not value.startswith(head + "-"):
            continue
        match = TRAILING_NUMBER.search(value)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def next_reference(model_label, field, prefix, *, institution=None,
                   parent=None, parent_field=None, digits=3):
    """Return the next ``PREFIX-ABBREV-001`` reference for a record.

    ``institution`` scopes the sequence per school. ``parent`` scopes it to a
    parent record (for example a curriculum framework) and adds that parent's
    code to the generated value.
    """
    parts = [prefix]
    namespace = f"klb:{model_label}:{field}"
    owner = "global"

    if institution is not None:
        parts.append(_token(institution.code or institution.name))
        namespace += f":institution:{institution.pk}"
        owner = f"institution:{institution.pk}"

    if parent is not None:
        parent_code = getattr(parent, "code", None) or getattr(parent, "pk", "X")
        parts.append(_token(parent_code, "P"))
        namespace += f":{parent._meta.label}:{parent.pk}"
        owner += f":parent:{parent.pk}"

    head = "-".join(parts)

    with transaction.atomic():
        _lock(namespace, owner)
        model = apps.get_model(model_label)
        filters = {}
        if institution is not None:
            filters["institution"] = institution
        if parent is not None and parent_field:
            filters[parent_field] = parent
        values = model.objects.using(connection.alias).filter(**filters).values_list(field, flat=True)
        sequence = _highest_number(values, head) + 1
    return f"{head}-{sequence:0{digits}d}"


def assign_reference(instance, field, model_label, prefix, **kwargs):
    """Fill ``field`` only when the caller left it blank."""
    if getattr(instance, field, None):
        return
    setattr(instance, field, next_reference(model_label, field, prefix, **kwargs))


def next_child_number(model_label, field, parent_field, parent):
    """Return the next sequential number within a parent (e.g. chapters)."""
    namespace = f"klb:{model_label}:{field}:{parent._meta.label}:{parent.pk}"
    with transaction.atomic():
        _lock(namespace, str(parent.pk))
        model = apps.get_model(model_label)
        highest = model.objects.using(connection.alias).filter(
            **{parent_field: parent}
        ).aggregate(highest=Max(field))["highest"]
    return (highest or 0) + 1


def assign_institution_code(instance):
    if instance.code:
        return
    base = school_abbreviation(instance.name)
    Institution = apps.get_model("institutions", "Institution")
    with transaction.atomic():
        _lock("klb:institutions:Institution:code", "global")
        taken = set(Institution.objects.values_list("code", flat=True))
        code = base
        suffix = 2
        while code in taken:
            code = f"{base}{suffix}"
            suffix += 1
    instance.code = code


def ensure_reference(instance):
    """Dispatch code generation based on the model class name.

    Called from model ``save()`` methods so API writes, management commands,
    the Django admin and shell scripts all get the same behaviour.
    """
    name = instance.__class__.__name__
    model_label = instance._meta.label

    if name == "Institution":
        assign_institution_code(instance)
        return

    if name == "InstitutionType":
        assign_reference(instance, "code", model_label, "TYP", digits=3)
        return

    if name == "Learner":
        institution = getattr(instance, "institution", None)
        if institution is None or institution.pk is None:
            raise ValueError("A learner needs an institution before references can be generated.")
        assign_reference(instance, "admission_number", model_label, "ADM", institution=institution)
        assign_reference(instance, "assessment_number", model_label, "ASM", institution=institution)
        return

    if name == "Teacher":
        institution = getattr(instance, "institution", None)
        if institution is None or institution.pk is None:
            raise ValueError("A teacher needs an institution before a staff number can be generated.")
        assign_reference(instance, "staff_number", model_label, "TCH", institution=institution)
        return

    if name == "Course":
        assign_reference(instance, "code", model_label, "CRS", institution=instance.institution)
        return

    if name == "Subject":
        assign_reference(instance, "code", model_label, "SUB", institution=instance.institution)
        return

    if name == "Department":
        assign_reference(instance, "code", model_label, "DEP", institution=instance.institution)
        return

    if name == "Publisher":
        assign_reference(instance, "code", model_label, "PUB", digits=4)
        return

    if name == "DigitalTextbook":
        # Real ISBNs are publisher-issued; this is a fallback catalogue ID.
        assign_reference(instance, "isbn", model_label, "TB", digits=6)
        return

    if name == "ContentAccess":
        assign_reference(instance, "licence_reference", model_label, "LIC", institution=instance.institution, digits=6)
        return

    if name == "CurriculumFramework":
        assign_reference(instance, "code", model_label, "CFW", digits=4)
        return

    if name == "EducationLevel":
        assign_reference(instance, "code", model_label, "LVL", parent=instance.framework,
                         parent_field="framework")
        return

    if name == "LearningArea":
        assign_reference(instance, "code", model_label, "LA", parent=instance.level, parent_field="level")
        return

    if name == "Strand":
        assign_reference(instance, "code", model_label, "STR", parent=instance.learning_area,
                         parent_field="learning_area")
        return

    if name == "SubStrand":
        assign_reference(instance, "code", model_label, "SS", parent=instance.strand, parent_field="strand")
        return

    if name == "LearningOutcome":
        assign_reference(instance, "code", model_label, "LO", parent=instance.sub_strand,
                         parent_field="sub_strand")
        return

    if name == "Competency":
        assign_reference(instance, "code", model_label, "CMP", parent=instance.framework,
                         parent_field="framework")
        return

    if name == "Chapter":
        Chapter = apps.get_model("content", "Chapter")
        clash = Chapter.objects.filter(
            textbook=instance.textbook, chapter_number=instance.chapter_number
        ).exclude(pk=instance.pk).exists()
        if not instance.chapter_number or clash:
            instance.chapter_number = next_child_number(
                model_label, "chapter_number", "textbook", instance.textbook
            )
        return

    # Generic fallback for newer apps that carry a business ``reference``.
    # A single concurrency-safe path avoids adding a dispatch branch for every
    # new ledger/document model. Institution-scoped models get a school token
    # so references cannot collide across schools.
    if hasattr(instance, "reference") and not instance.reference:
        prefixes = {
            "FeeStructure": "FEE",
            "FeeInvoice": "INV",
            "Payment": "PAY",
            "ApprovalRequest": "APR",
            "ApprovalDecision": "APD",
            "ApprovalChecklistItem": "ACL",
            "KemisExport": "KEM",
            "KemisFieldMapping": "KFM",
            "TutorConversation": "TUT",
            "TutorMessage": "TMSG",
            "AnalyticsSnapshot": "ANA",
            "RemediationRule": "RMR",
            "RemediationTask": "RMT",
        }
        options = {"digits": 5}
        institution = getattr(instance, "institution", None)
        if institution is not None:
            options["institution"] = institution
        assign_reference(instance, "reference", model_label,
                         prefixes.get(name, name[:4].upper()), **options)
