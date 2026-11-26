"""Read-only data-quality scans and a small allowlist of safe auto-fixes.

The console never deletes records. Scans return counts and samples; fixes
apply only to fields whose value can be reconstructed from the record itself
(surrounding whitespace, or an admission date derived from the created date).
Every applied change is recorded through the shared field-level audit helper.
"""
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.core.audit import record_change
from apps.fees.models import FeeInvoice, Payment
from apps.guardians.models import Guardian
from apps.learners.models import GuardianLinkRequest, Learner, LearnerGuardian
from apps.teachers.models import Teacher
from apps.accounts.models import User

SAFE_FIXES = {
    "identifier_whitespace": "Remove leading and trailing spaces from identifier fields.",
    "learner_admitted_date": "Fill a missing admission date from the learner record's creation date.",
}

IDENTIFIER_FIELDS = [
    (Learner, ["admission_number", "assessment_number"]),
    (Teacher, ["staff_number"]),
    (Guardian, ["guardian_number"]),
]


def _issue(code, label, severity, count, samples=None, fixable=False, detail=""):
    return {
        "code": code,
        "label": label,
        "severity": severity,
        "count": count,
        "samples": samples or [],
        "fixable": fixable,
        "detail": detail,
    }


def _sample(items, formatter, limit=5):
    return [formatter(item) for item in items[:limit]]


def scan_institution(institution):
    """Return data-quality issues for one school. Never changes data."""
    today = timezone.localdate()
    issues = []

    duplicates = (
        Learner.objects.filter(institution=institution)
        .exclude(admission_number="")
        .values("admission_number")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    issues.append(_issue(
        "duplicate_admission_number", "Duplicate admission numbers", "error",
        duplicates.count(),
        _sample(duplicates, lambda row: f"{row['admission_number']} ({row['count']} records)"),
        detail="Each learner in a school needs a unique admission number.",
    ))

    staff_duplicates = (
        Teacher.objects.filter(institution=institution)
        .exclude(staff_number="")
        .values("staff_number")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    issues.append(_issue(
        "duplicate_staff_number", "Duplicate staff numbers", "error",
        staff_duplicates.count(),
        _sample(staff_duplicates, lambda row: f"{row['staff_number']} ({row['count']} records)"),
    ))

    missing_ids = Learner.objects.filter(institution=institution).filter(
        Q(admission_number="") | Q(assessment_number="")
    )
    issues.append(_issue(
        "missing_learner_identifier", "Learners missing an identifier", "error",
        missing_ids.count(),
        _sample(missing_ids.values_list("id", flat=True), lambda pk: f"Learner #{pk}"),
    ))

    learner_ids = set(
        Learner.objects.filter(institution=institution).values_list("user_id", flat=True)
    )
    orphans = User.objects.filter(institution=institution, role="LEARNER").exclude(
        pk__in=learner_ids
    )
    issues.append(_issue(
        "orphan_learner_account", "Learner accounts without a learner record", "warning",
        orphans.count(),
        _sample(orphans.values_list("username", flat=True), lambda name: str(name)),
    ))

    stale_requests = GuardianLinkRequest.objects.filter(
        institution=institution, status="PENDING",
        created_at__lt=timezone.now() - timedelta(days=14),
    )
    issues.append(_issue(
        "stale_link_request", "Guardian link requests waiting over 14 days", "warning",
        stale_requests.count(),
        _sample(stale_requests.values_list("reference", flat=True), lambda ref: str(ref)),
    ))

    active_learners = Learner.objects.filter(
        institution=institution, status="ACTIVE", is_archived=False
    )
    primary_ids = set(
        LearnerGuardian.objects.filter(
            is_verified=True, is_primary=True, learner__institution=institution
        ).values_list("learner_id", flat=True)
    )
    without_primary = active_learners.exclude(pk__in=primary_ids)
    issues.append(_issue(
        "learner_without_primary_guardian", "Active learners without a primary guardian", "warning",
        without_primary.count(),
        _sample(
            without_primary.values_list("admission_number", flat=True),
            lambda number: str(number),
        ),
    ))

    overdue_invoices = FeeInvoice.objects.filter(
        institution=institution, status__in=["PENDING", "PARTIAL"], due_date__lt=today
    )
    issues.append(_issue(
        "overdue_invoice", "Overdue fee invoices", "warning",
        overdue_invoices.count(),
        _sample(overdue_invoices.values_list("reference", flat=True), lambda ref: str(ref)),
    ))

    unconfirmed = Payment.objects.filter(
        institution=institution, method="MOBILE", transaction_reference=""
    )
    issues.append(_issue(
        "mobile_payment_without_reference", "Mobile payments without a transaction code", "warning",
        unconfirmed.count(),
        _sample(unconfirmed.values_list("reference", flat=True), lambda ref: str(ref)),
    ))

    whitespace_samples = []
    whitespace_count = 0
    for model, fields in IDENTIFIER_FIELDS:
        for field in fields:
            rows = [
                (pk, value) for pk, value in model.objects.filter(
                    institution=institution
                ).exclude(**{f"{field}__exact": ""}).values_list("pk", field)
                if value and value != value.strip()
            ]
            whitespace_count += len(rows)
            whitespace_samples.extend(
                f"{model.__name__}.{field} #{pk}" for pk, _ in rows[:3]
            )
    issues.append(_issue(
        "identifier_whitespace", "Identifiers with surrounding spaces", "warning",
        whitespace_count, whitespace_samples[:5], fixable=True, detail=SAFE_FIXES["identifier_whitespace"],
    ))

    missing_dates = Learner.objects.filter(institution=institution, date_admitted__isnull=True)
    issues.append(_issue(
        "learner_admitted_date", "Learners without an admission date", "info",
        missing_dates.count(),
        _sample(missing_dates.values_list("admission_number", flat=True), lambda number: str(number)),
        fixable=True, detail=SAFE_FIXES["learner_admitted_date"],
    ))

    return {
        "institution_id": institution.pk,
        "institution_name": institution.name,
        "issues": issues,
        "total": sum(1 for issue in issues if issue["count"]),
    }


def preview_fix(institution, code):
    """List the exact changes a safe fix would make, without writing."""
    if code not in SAFE_FIXES:
        raise ValueError("Unknown or unsafe fix.")
    changes = _fix_changes(institution, code)
    return {
        "code": code,
        "description": SAFE_FIXES[code],
        "change_count": len(changes),
        "changes": changes[:20],
        "applied": False,
    }


def _fix_changes(institution, code):
    changes = []
    if code == "identifier_whitespace":
        for model, fields in IDENTIFIER_FIELDS:
            for field in fields:
                rows = model.objects.filter(institution=institution).exclude(
                    **{f"{field}__exact": ""}
                ).values_list("pk", field)
                for pk, value in rows:
                    if value and value != value.strip():
                        changes.append({
                            "entity_type": model.__name__, "entity_id": pk,
                            "field": field, "before": value, "after": value.strip(),
                        })
    elif code == "learner_admitted_date":
        for learner in Learner.objects.filter(
            institution=institution, date_admitted__isnull=True
        ).only("pk", "created_at"):
            changes.append({
                "entity_type": "Learner", "entity_id": learner.pk,
                "field": "date_admitted", "before": None,
                "after": learner.created_at.date().isoformat(),
            })
    return changes


@transaction.atomic
def apply_fix(institution, code, actor=None, request=None):
    """Apply one allowlisted fix atomically and record every field change."""
    if code not in SAFE_FIXES:
        raise ValueError("Unknown or unsafe fix.")
    changes = _fix_changes(institution, code)
    models = {model.__name__: model for model, _ in IDENTIFIER_FIELDS}
    models["Learner"] = Learner
    applied = 0
    for change in changes:
        model = models[change["entity_type"]]
        instance = model.objects.get(pk=change["entity_id"])
        field = change["field"]
        new_value = change["after"]
        if field == "date_admitted":
            new_value = date.fromisoformat(new_value)
        before = {field: getattr(instance, field)}
        setattr(instance, field, new_value)
        instance.save(update_fields=[field, "updated_at"])
        record_change(
            actor, instance, before, {field: new_value},
            action="data_quality.fixed", request=request,
        )
        applied += 1
    return {
        "code": code,
        "description": SAFE_FIXES[code],
        "change_count": applied,
        "changes": changes[:20],
        "applied": True,
    }
