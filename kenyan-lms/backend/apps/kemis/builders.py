"""Row builders for the six local KEMIS-style datasets.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.

``DEFAULT_COLUMNS`` below is a *local* starting point, not an official schema.
An active ``KemisFieldMapping`` row overrides it when mappings are supplied.
"""
import re
from datetime import date, datetime, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Count

from apps.assessments.models import ExamResult
from apps.attendance.models import AttendanceRecord
from apps.institutions.models import SchoolClass
from apps.kemis.models import DATASET_CHOICES
from apps.learners.models import Learner
from apps.teachers.models import Teacher

DATASET_LABELS = dict(DATASET_CHOICES)

# (dotted source path, local target column). These are deliberately simple,
# documented defaults; they are not a claim about any official template.
DEFAULT_COLUMNS = {
    "LEARNERS": [
        ("admission_number", "ADMISSION_NUMBER"),
        ("assessment_number", "ASSESSMENT_NUMBER"),
        ("user.full_name", "LEARNER_NAME"),
        ("gender", "GENDER"),
        ("date_of_birth", "DATE_OF_BIRTH"),
        ("class_room.name", "CLASS"),
        ("status", "STATUS"),
        ("date_admitted", "DATE_ADMITTED"),
    ],
    "TEACHERS": [
        ("staff_number", "STAFF_NUMBER"),
        ("user.full_name", "TEACHER_NAME"),
        ("employment_type", "EMPLOYMENT_TYPE"),
        ("phone", "PHONE"),
        ("is_active", "IS_ACTIVE"),
    ],
    "INSTITUTION": [
        ("code", "INSTITUTION_CODE"),
        ("name", "INSTITUTION_NAME"),
        ("institution_type.name", "INSTITUTION_TYPE"),
        ("county", "COUNTY"),
        ("town", "TOWN"),
        ("email", "EMAIL"),
        ("phone", "PHONE"),
        ("address_line", "ADDRESS"),
        ("postal_code", "POSTAL_CODE"),
        ("is_active", "IS_ACTIVE"),
    ],
    "ENROLLMENT": [
        ("name", "CLASS_NAME"),
        ("level", "LEVEL"),
        ("stream", "STREAM"),
        ("academic_year.name", "ACADEMIC_YEAR"),
        ("capacity", "CAPACITY"),
        ("enrolled_count", "ENROLLED_LEARNERS"),
    ],
    "ATTENDANCE": [
        ("learner.admission_number", "ADMISSION_NUMBER"),
        ("learner.user.full_name", "LEARNER_NAME"),
        ("date", "DATE"),
        ("status", "STATUS"),
        ("school_class.name", "CLASS"),
        ("term.name", "TERM"),
        ("marked_by.full_name", "MARKED_BY"),
    ],
    "RESULTS": [
        ("learner.admission_number", "ADMISSION_NUMBER"),
        ("learner.user.full_name", "LEARNER_NAME"),
        ("exam.title", "EXAM"),
        ("exam.subject.name", "SUBJECT"),
        ("score", "SCORE"),
        ("grade", "GRADE"),
        ("position", "POSITION"),
        ("exam.exam_date", "EXAM_DATE"),
    ],
}

# Only these keys from the JSON ``filters`` body reach the ORM. Anything else
# is ignored, so a client cannot construct arbitrary database lookups.
FILTER_FIELDS = {
    "LEARNERS": {
        "status": "status", "gender": "gender", "admission_number": "admission_number",
        "class_room": "class_room_id", "school_class": "class_room_id",
    },
    "TEACHERS": {"is_active": "is_active", "employment_type": "employment_type"},
    "INSTITUTION": {},
    "ENROLLMENT": {"level": "level", "name": "name", "academic_year": "academic_year_id"},
    "ATTENDANCE": {
        "status": "status", "learner": "learner_id", "school_class": "school_class_id",
        "term": "term_id", "date": "date", "date_from": "date__gte", "date_to": "date__lte",
    },
    "RESULTS": {
        "exam": "exam_id", "learner": "learner_id", "grade": "grade",
        "date_from": "exam__exam_date__gte", "date_to": "exam__exam_date__lte",
    },
}

_SAFE_ATTRIBUTE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _resolve(obj, path):
    """Resolve a dotted attribute path with getattr only - never eval."""
    current = obj
    for part in str(path or "").split("."):
        if not _SAFE_ATTRIBUTE.match(part):
            return None
        current = getattr(current, part, None)
        if current is None or callable(current):
            return None
    return current


def _stringify(value):
    """Give CSV and JSON payloads stable, readable scalar values."""
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _mapping_values(item):
    if isinstance(item, dict):
        return {
            "dataset": item.get("dataset"),
            "source": item.get("source_field"),
            "target": item.get("target_column"),
            "active": item.get("is_active", True),
        }
    return {
        "dataset": getattr(item, "dataset", None),
        "source": getattr(item, "source_field", None),
        "target": getattr(item, "target_column", None),
        "active": getattr(item, "is_active", True),
    }


def _columns(dataset, mappings):
    """Use active supplied mappings for this dataset, else local defaults."""
    if mappings is not None:
        try:
            candidates = list(mappings)
        except TypeError:
            candidates = []
        chosen = []
        for item in candidates:
            values = _mapping_values(item)
            if not values["active"]:
                continue
            if values["dataset"] and values["dataset"] != dataset:
                continue
            if values["source"] and values["target"]:
                chosen.append((values["source"], values["target"]))
        if chosen:
            return chosen
    return list(DEFAULT_COLUMNS.get(dataset, []))


def default_columns(dataset):
    """Describe the local fallback columns in the same shape as mappings."""
    return [
        {"source_field": source, "target_column": target, "is_required": False}
        for source, target in DEFAULT_COLUMNS.get(dataset, [])
    ]


def _apply_filters(queryset, dataset, filters):
    if not isinstance(filters, dict):
        return queryset
    allowed = FILTER_FIELDS.get(dataset, {})
    for key, value in filters.items():
        orm_field = allowed.get(key)
        if not orm_field or value is None or value == "":
            continue
        try:
            queryset = queryset.filter(**{orm_field: value})
        except (ValueError, TypeError, ValidationError):
            # A malformed filter is ignored rather than crashing an export.
            continue
    return queryset


def _source_objects(dataset, institution, filters):
    if institution is None:
        return []
    if dataset == "LEARNERS":
        queryset = Learner.objects.filter(institution=institution).select_related("user", "class_room")
    elif dataset == "TEACHERS":
        queryset = Teacher.objects.filter(institution=institution).select_related("user")
    elif dataset == "INSTITUTION":
        return [institution]
    elif dataset == "ENROLLMENT":
        queryset = (
            SchoolClass.objects.filter(institution=institution)
            .select_related("academic_year")
            .annotate(enrolled_count=Count("learners"))
        )
    elif dataset == "ATTENDANCE":
        queryset = AttendanceRecord.objects.filter(institution=institution).select_related(
            "learner__user", "school_class", "term", "marked_by",
        )
    elif dataset == "RESULTS":
        queryset = ExamResult.objects.filter(institution=institution).select_related(
            "learner__user", "exam__subject", "exam__term",
        )
    else:
        raise ValueError(f"Unsupported KEMIS dataset: {dataset!r}")
    return _apply_filters(queryset, dataset, filters)


def build_rows(dataset, institution, filters=None, mappings=None):
    """Return ``(headers, rows)`` for one institution-scoped dataset.

    ``mappings`` may be a queryset of ``KemisFieldMapping`` objects or plain
    dictionaries with ``source_field``/``target_column`` keys. Inactive
    mappings and mappings for another dataset are skipped. When no usable
    mapping exists, ``DEFAULT_COLUMNS`` is used.
    """
    dataset = str(dataset or "").upper()
    if dataset not in DATASET_LABELS:
        raise ValueError(f"Unsupported KEMIS dataset: {dataset!r}")

    columns = _columns(dataset, mappings)
    headers = [target for _, target in columns]
    rows = [
        [_stringify(_resolve(obj, source)) for source, _ in columns]
        for obj in _source_objects(dataset, institution, filters)
    ]
    return headers, rows
