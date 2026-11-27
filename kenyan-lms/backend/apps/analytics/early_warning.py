"""Transparent, rule-based early warning over existing school records.

The rules are deliberately simple and auditable: every signal carries its
threshold and the points it contributed. Nothing here predicts a future
outcome; staff can see exactly why a learner was flagged and can dismiss a
flag without losing its evidence.
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Q
from django.utils import timezone

from apps.analytics.models import InterventionTask
from apps.assessments.models import ExamResult, QuizAttempt
from apps.attendance.models import AttendanceRecord
from apps.communications.services import notify_users
from apps.core.audit import log_audit
from apps.core.constants import Roles
from apps.courses.models import Assignment, LessonProgress, Submission
from apps.fees.models import FeeInvoice
from apps.learners.models import Learner

# Points are additive. Thresholds are documented in the admin guide and shown
# in the UI next to each signal so staff can explain a flag to a parent.
RULES = {
    "ATTENDANCE": {
        "label": "Low attendance",
        "description": "Above 20% absent over 30 days with at least 5 marked days.",
        "window_days": 30,
        "absent_rate_above": 0.20,
        "points": 3,
        "action": "Check attendance register and speak to the learner.",
    },
    "ASSESSMENT": {
        "label": "Low assessment scores",
        "description": "Any exam or completed quiz result below 50%.",
        "pass_mark": 0.50,
        "points": 3,
        "action": "Review recent work and arrange targeted practice.",
    },
    "SUBMISSION": {
        "label": "Missing assignment submissions",
        "description": "At least one published assignment past its due date with no submission.",
        "min_missing": 1,
        "points": 2,
        "action": "Check overdue assignments and provide a catch-up plan.",
    },
    "PROGRESS": {
        "label": "Low lesson completion",
        "description": "Below 30% of lessons completed across at least 3 recorded lessons.",
        "completion_below": 0.30,
        "min_lessons": 3,
        "points": 2,
        "action": "Review lesson progress and remove blockers.",
    },
    "FEES": {
        "label": "Overdue fee balance",
        "description": "An unpaid invoice more than 7 days past its due date.",
        "days_overdue": 7,
        "points": 1,
        "action": "Speak to the family office about the overdue invoice.",
    },
}


def level_for_score(score):
    if score >= 6:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    if score >= 1:
        return "LOW"
    return "NONE"


def _ratio(score, maximum):
    """Return a 0-1 mastery ratio, or None when the maximum is unusable."""
    try:
        numerator = Decimal(str(score or 0))
        denominator = Decimal(str(maximum or 0))
        if denominator <= 0:
            return None
        return numerator / denominator
    except (InvalidOperation, TypeError, ValueError):
        return None


def _attendance_signals(institution, learners, today):
    start = today - timedelta(days=RULES["ATTENDANCE"]["window_days"])
    rows = (
        AttendanceRecord.objects.filter(
            institution=institution, learner__in=learners, date__gte=start, date__lte=today
        )
        .values("learner_id")
        .annotate(
            total=Count("id"),
            absent=Count("id", filter=Q(status="ABSENT")),
        )
    )
    result = {}
    threshold = RULES["ATTENDANCE"]["absent_rate_above"]
    for row in rows:
        rate = row["absent"] / row["total"] if row["total"] else 0
        if row["total"] >= 5 and rate > threshold:
            result[row["learner_id"]] = {
                "code": "ATTENDANCE",
                "label": RULES["ATTENDANCE"]["label"],
                "detail": (
                    f"{row['absent']} of {row['total']} days absent in the last "
                    f"{RULES['ATTENDANCE']['window_days']} days "
                    f"({round(rate * 100)}%, threshold {round(threshold * 100)}%)."
                ),
                "points": RULES["ATTENDANCE"]["points"],
            }
    return result


def _assessment_signals(institution, learners):
    threshold = RULES["ASSESSMENT"]["pass_mark"]
    failures = {}
    results = ExamResult.objects.filter(learner__in=learners).values_list(
        "learner_id", "score", "exam__max_score"
    )
    attempts = QuizAttempt.objects.filter(
        learner__in=learners, status__in=["COMPLETED", "SYNCED"]
    ).values_list("learner_id", "score", "max_score")
    for learner_id, score, maximum in list(results) + list(attempts):
        ratio = _ratio(score, maximum)
        if ratio is not None and ratio < threshold:
            failures[learner_id] = failures.get(learner_id, 0) + 1
    return {
        learner_id: {
            "code": "ASSESSMENT",
            "label": RULES["ASSESSMENT"]["label"],
            "detail": (
                f"{count} recent result(s) below "
                f"{round(threshold * 100)}% pass mark."
            ),
            "points": RULES["ASSESSMENT"]["points"],
        }
        for learner_id, count in failures.items()
    }


def _submission_signals(institution, learners, now):
    overdue = Assignment.objects.filter(
        course__institution=institution, is_published=True, due_date__lt=now
    )
    submitted = set(
        Submission.objects.filter(
            assignment__in=overdue, status__in=["SUBMITTED", "GRADED", "RETURNED"]
        ).values_list("learner_id", "assignment_id")
    )
    overdue_ids = list(overdue.values_list("id", flat=True))
    missing = {}
    for learner in learners:
        count = sum(
            1 for assignment_id in overdue_ids
            if (learner.pk, assignment_id) not in submitted
        )
        if count:
            missing[learner.pk] = count
    minimum = RULES["SUBMISSION"]["min_missing"]
    return {
        learner_id: {
            "code": "SUBMISSION",
            "label": RULES["SUBMISSION"]["label"],
            "detail": f"{count} overdue assignment(s) without a submission.",
            "points": RULES["SUBMISSION"]["points"],
        }
        for learner_id, count in missing.items()
        if count >= minimum
    }


def _progress_signals(institution, learners):
    rule = RULES["PROGRESS"]
    rows = (
        LessonProgress.objects.filter(institution=institution, learner__in=learners)
        .values("learner_id")
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status="COMPLETED")),
        )
    )
    result = {}
    for row in rows:
        if row["total"] < rule["min_lessons"]:
            continue
        rate = row["completed"] / row["total"]
        if rate < rule["completion_below"]:
            result[row["learner_id"]] = {
                "code": "PROGRESS",
                "label": rule["label"],
                "detail": (
                    f"{row['completed']} of {row['total']} lessons completed "
                    f"({round(rate * 100)}%, threshold "
                    f"{round(rule['completion_below'] * 100)}%)."
                ),
                "points": rule["points"],
            }
    return result


def _fee_signals(institution, learners, today):
    rule = RULES["FEES"]
    cutoff = today.date() - timedelta(days=rule["days_overdue"])
    invoices = FeeInvoice.objects.filter(
        institution=institution,
        learner__in=learners,
        status__in=["PENDING", "PARTIAL"],
        due_date__lt=cutoff,
    ).values("learner_id", "amount_due", "amount_paid")
    totals = {}
    for invoice in invoices:
        balance = invoice["amount_due"] - invoice["amount_paid"]
        if balance > 0:
            totals[invoice["learner_id"]] = totals.get(invoice["learner_id"], Decimal("0")) + balance
    return {
        learner_id: {
            "code": "FEES",
            "label": rule["label"],
            "detail": f"Outstanding balance {balance:.2f} more than {rule['days_overdue']} days overdue.",
            "points": rule["points"],
        }
        for learner_id, balance in totals.items()
    }


def build_early_warning(institution, params=None):
    """Compute risk alerts for active learners in one institution."""
    params = params or {}
    today = timezone.localdate()
    learners = list(
        Learner.objects.filter(
            institution=institution, status="ACTIVE", is_archived=False
        ).select_related("user", "class_room")
    )
    by_id = {learner.pk: learner for learner in learners}
    signal_sets = [
        _attendance_signals(institution, learners, today),
        _assessment_signals(institution, learners),
        _submission_signals(institution, learners, timezone.now()),
        _progress_signals(institution, learners),
        _fee_signals(institution, learners, timezone.now()),
    ]
    open_tasks = {
        row["learner_id"]: row["count"]
        for row in InterventionTask.objects.filter(
            institution=institution, status__in=["OPEN", "ASSIGNED"]
        ).values("learner_id").annotate(count=Count("id"))
    }
    alerts = []
    for learner_id, learner in by_id.items():
        signals = [item for item in (signals.get(learner_id) for signals in signal_sets) if item]
        signals.sort(key=lambda item: (-item["points"], item["code"]))
        score = sum(item["points"] for item in signals)
        level = level_for_score(score)
        if level == "NONE":
            continue
        alerts.append({
            "learner_id": learner_id,
            "learner_name": learner.user.full_name,
            "admission_number": learner.admission_number,
            "class_room_id": learner.class_room_id,
            "class_name": learner.class_room.display_name if learner.class_room_id else "",
            "risk_score": score,
            "risk_level": level,
            "signals": signals,
            "recommended_action": RULES.get(signals[0]["code"], {}).get("action", ""),
            "open_task_count": open_tasks.get(learner_id, 0),
        })
    level_filter = (params.get("risk_level") or "").upper()
    if level_filter in {"LOW", "MEDIUM", "HIGH"}:
        alerts = [alert for alert in alerts if alert["risk_level"] == level_filter]
    class_filter = params.get("class_room")
    if class_filter:
        alerts = [alert for alert in alerts if str(alert.get("class_room_id", "")) == str(class_filter)]
    alerts.sort(key=lambda item: (-item["risk_score"], item["learner_name"]))
    return {
        "rules": RULES,
        "summary": {
            "high": sum(1 for alert in alerts if alert["risk_level"] == "HIGH"),
            "medium": sum(1 for alert in alerts if alert["risk_level"] == "MEDIUM"),
            "low": sum(1 for alert in alerts if alert["risk_level"] == "LOW"),
            "total": len(alerts),
            "learners_checked": len(learners),
        },
        "alerts": alerts,
    }


def refresh_early_warning(institution, actor=None, request=None):
    """Recompute flags and create one open intervention task per flagged learner."""
    report = build_early_warning(institution)
    created = []
    for alert in report["alerts"]:
        if alert["risk_level"] not in {"HIGH", "MEDIUM"} or alert["open_task_count"]:
            continue
        task = InterventionTask.objects.create(
            institution=institution,
            learner_id=alert["learner_id"],
            risk_level=alert["risk_level"],
            risk_score=alert["risk_score"],
            signals=alert["signals"],
            notes=alert["recommended_action"],
            due_date=timezone.localdate() + timedelta(days=7 if alert["risk_level"] == "HIGH" else 14),
        )
        created.append(task)
        alert["open_task_count"] = 1
    if created:
        admins = [
            user for user in institution.users.filter(
                role__in=[Roles.ADMIN, Roles.SUPER_ADMIN], is_active=True
            )
        ]
        notify_users(
            admins,
            "Learners needing attention",
            "New support tasks were created. Review the dashboard to see which "
            "learners may need additional guidance.",
            "SYSTEM",
            "/admin/early-warning",
        )
    log_audit(
        actor, "early_warning.refreshed", "InterventionTask", None,
        {
            "alerts": report["summary"]["total"],
            "tasks_created": len(created),
            "rules": sorted(RULES),
        },
        institution=institution, request=request,
    )
    report["tasks_created"] = len(created)
    return report
