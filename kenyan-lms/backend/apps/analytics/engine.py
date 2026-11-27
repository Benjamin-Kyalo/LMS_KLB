"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting.

Assumptions, all derived from the existing models:

* ``CompetencyEvidence.achieved_level`` is mapped to a 0-1 mastery scale:
  BEGINNING 0.25, DEVELOPING 0.50, ACHIEVING 0.75, EXTENDING 1.00. When the
  level is blank, a linked rubric level's ``min_score / max_score`` is used.
* ``ExamResult`` and ``QuizAttempt`` ratios are ``score / max_score`` (0-1).
  Those records have no competency foreign key, so their signal is an
  institution-wide average for the learner, not a per-competency score.
* Cohort mastery and result averages are reported as percentages (0-100);
  attendance percentage is PRESENT records / all attendance records.
* ``min_attempts`` is the number of scored records required per signal before
  a learner can be flagged.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from apps.analytics.models import AnalyticsSnapshot, RemediationRule, RemediationTask
from apps.assessments.models import ExamResult, QuizAttempt
from apps.attendance.models import AttendanceRecord
from apps.core.constants import AttendanceStatus, MasteryLevel
from apps.curriculum.models import Competency, CompetencyEvidence
from apps.learners.models import Learner
from apps.reports.analytics import attendance_status_series, exam_series

ZERO = Decimal("0")
HUNDRED = Decimal("100")
MASTERY_SCORES = {
    MasteryLevel.BEGINNING: Decimal("0.25"),
    MasteryLevel.DEVELOPING: Decimal("0.50"),
    MasteryLevel.ACHIEVING: Decimal("0.75"),
    MasteryLevel.EXTENDING: Decimal("1.00"),
}
CLOSED_STATUSES = {RemediationTask.COMPLETED, RemediationTask.DISMISSED}
# Badge displays are derived, never awarded by this code. Only the two highest
# bands count as earned; lower bands show progress toward a badge.
BADGE_LEVEL_ORDER = (
    MasteryLevel.BEGINNING,
    MasteryLevel.DEVELOPING,
    MasteryLevel.ACHIEVING,
    MasteryLevel.EXTENDING,
)
EARNED_BADGE_LEVELS = {MasteryLevel.ACHIEVING, MasteryLevel.EXTENDING}


def _decimal(value):
    """Return a Decimal for a stored numeric value, or None if unusable."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _ratio(numerator, denominator):
    top = _decimal(numerator)
    bottom = _decimal(denominator)
    if top is None or bottom is None or bottom <= ZERO:
        return None
    return top / bottom


def _average(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values, ZERO) / Decimal(len(values))


def _number(value):
    return None if value is None else round(float(value), 1)


def _positive_id(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _mastery_from_evidence(item):
    """Convert one evidence row to the shared 0-1 mastery scale."""
    level = getattr(item, "achieved_level", None)
    score = MASTERY_SCORES.get(level)
    if score is not None:
        return score
    rubric = getattr(item, "rubric_level", None)
    if rubric is None:
        return None
    maximum = getattr(rubric, "max_score", None)
    return _ratio(getattr(rubric, "min_score", None), maximum if maximum is not None else HUNDRED)


def _learner_evidence_stats(institution, competency_id=None, learner_ids=None):
    """Return per-learner evidence counts, level counts and 0-1 scores."""
    queryset = CompetencyEvidence.objects.filter(institution=institution).select_related("rubric_level")
    if competency_id:
        queryset = queryset.filter(competency_id=competency_id)
    if learner_ids is not None:
        queryset = queryset.filter(learner_id__in=learner_ids)

    stats = defaultdict(lambda: {"attempts": 0, "scores": [], "levels": defaultdict(int), "ids": []})
    for item in queryset:
        learner_id = getattr(item, "learner_id", None)
        if learner_id is None:
            continue
        bucket = stats[learner_id]
        bucket["attempts"] += 1
        level = getattr(item, "achieved_level", None) or "UNSPECIFIED"
        bucket["levels"][level] += 1
        if len(bucket["ids"]) < 20:
            bucket["ids"].append(item.pk)
        score = _mastery_from_evidence(item)
        if score is not None:
            bucket["scores"].append(score)
    return stats


def _badge_level(score):
    """Resolve an average 0-1 mastery score to its highest achieved band."""
    if score is None:
        return None
    for level in reversed(BADGE_LEVEL_ORDER):
        if score >= MASTERY_SCORES[level]:
            return level
    return None


def build_mastery_badges(institution, filters=None):
    """Derive badge displays from competency evidence; write nothing.

    Evidence is grouped by learner and competency and scored with the same
    0-1 mapping used by analytics. Badges are a transparent display of those
    records, not an awarded credential: this function never creates a row,
    notification or audit entry, and rubric grades are never converted into
    competency evidence here.
    """
    filters = filters or {}
    queryset = CompetencyEvidence.objects.filter(
        institution=institution, competency__isnull=False
    ).select_related("competency", "learner", "learner__user")

    learner_id = _positive_id(filters.get("learner"))
    competency_id = _positive_id(filters.get("competency"))
    mastery_level = str(filters.get("mastery_level") or "").strip().upper()
    if mastery_level and mastery_level not in MASTERY_SCORES:
        raise ValueError("Choose a valid mastery level.")
    if learner_id:
        queryset = queryset.filter(learner_id=learner_id)
    if competency_id:
        queryset = queryset.filter(competency_id=competency_id)

    buckets = defaultdict(lambda: {"scores": [], "ids": [], "count": 0, "recent": None})
    learner_ids = set()
    competency_ids = set()
    for item in queryset:
        key = (item.learner_id, item.competency_id)
        bucket = buckets[key]
        bucket["count"] += 1
        learner_ids.add(item.learner_id)
        competency_ids.add(item.competency_id)
        if len(bucket["ids"]) < 20:
            bucket["ids"].append(item.pk)
        if bucket["recent"] is None or item.recorded_at > bucket["recent"]:
            bucket["recent"] = item.recorded_at
        score = _mastery_from_evidence(item)
        if score is not None:
            bucket["scores"].append(score)

    learners = {
        row.pk: row for row in Learner.objects.filter(pk__in=learner_ids).select_related("user")
    }
    competencies = {
        row.pk: row for row in Competency.objects.filter(pk__in=competency_ids)
    }

    badges = []
    for (row_learner_id, row_competency_id), bucket in buckets.items():
        score = _average(bucket["scores"])
        level = _badge_level(score)
        if level is None or (mastery_level and level != mastery_level):
            continue
        learner = learners.get(row_learner_id)
        competency = competencies.get(row_competency_id)
        user = getattr(learner, "user", None)
        name = getattr(user, "full_name", None) or (
            user.get_full_name() if user else ""
        ) or str(user or "Learner")
        badges.append({
            "learner_id": row_learner_id,
            "learner_name": name,
            "admission_number": getattr(learner, "admission_number", ""),
            "competency_id": row_competency_id,
            "competency_name": getattr(competency, "name", "Competency"),
            "mastery_level": level,
            "mastery_score": round(float(score), 4),
            "score_percent": _number(score * HUNDRED),
            "evidence_count": bucket["count"],
            "evidence_ids": bucket["ids"],
            "recent_evidence_at": bucket["recent"].isoformat() if bucket["recent"] else None,
            "earned": level in EARNED_BADGE_LEVELS,
        })

    badges.sort(key=lambda row: (
        str(row["learner_name"]).lower(), str(row["competency_name"]).lower(),
        row["learner_id"], row["competency_id"],
    ))
    by_level = {level: 0 for level in BADGE_LEVEL_ORDER}
    for badge in badges:
        by_level[badge["mastery_level"]] += 1

    return {
        "scope": {"institution_id": institution.pk, "institution": institution.name},
        "rules": {
            "source": "CompetencyEvidence",
            "mastery_scores": {level: str(score) for level, score in MASTERY_SCORES.items()},
            "badge_bands": [
                {
                    "code": level,
                    "min_score": str(MASTERY_SCORES[level]),
                    "earned": level in EARNED_BADGE_LEVELS,
                }
                for level in BADGE_LEVEL_ORDER
            ],
            "note": "Badges are derived displays, not awarded credentials.",
        },
        "summary": {
            "learners": len({badge["learner_id"] for badge in badges}),
            "badges": len(badges),
            "earned_badges": sum(1 for badge in badges if badge["earned"]),
            "by_level": by_level,
        },
        "badges": badges,
    }


def _learner_result_stats(institution, learner_ids=None, subject_id=None, term_id=None):
    """Return per-learner exam/quiz ratios grouped by subject id."""
    exams = ExamResult.objects.filter(institution=institution).select_related("exam", "exam__subject")
    quizzes = QuizAttempt.objects.filter(institution=institution).select_related("quiz", "quiz__subject")
    if learner_ids is not None:
        exams = exams.filter(learner_id__in=learner_ids)
        quizzes = quizzes.filter(learner_id__in=learner_ids)
    if subject_id is not None:
        exams = exams.filter(exam__subject_id=subject_id)
        quizzes = quizzes.filter(quiz__subject_id=subject_id)
    if term_id is not None:
        exams = exams.filter(exam__term_id=term_id)

    def new_bucket():
        return {
            "attempts": 0,
            "ratios": [],
            "by_subject": defaultdict(list),
            "subjects": set(),
            "ids": [],
        }

    stats = defaultdict(new_bucket)
    for result in exams:
        exam = getattr(result, "exam", None)
        ratio = _ratio(getattr(result, "score", None), getattr(exam, "max_score", None))
        if ratio is None:
            continue
        subject = getattr(exam, "subject_id", None)
        subject_name = getattr(getattr(exam, "subject", None), "name", None) or "Unassigned"
        bucket = stats[result.learner_id]
        bucket["attempts"] += 1
        bucket["ratios"].append(ratio)
        bucket["by_subject"][subject].append(ratio)
        bucket["subjects"].add((subject, subject_name))
        if len(bucket["ids"]) < 20:
            bucket["ids"].append(result.pk)

    for attempt in quizzes:
        status = getattr(attempt, "status", None)
        if status and status not in ("COMPLETED", "SYNCED"):
            continue
        quiz = getattr(attempt, "quiz", None)
        ratio = _ratio(getattr(attempt, "score", None), getattr(quiz, "max_score", None))
        if ratio is None:
            continue
        subject = getattr(quiz, "subject_id", None)
        subject_name = getattr(getattr(quiz, "subject", None), "name", None) or "Unassigned"
        bucket = stats[attempt.learner_id]
        bucket["attempts"] += 1
        bucket["ratios"].append(ratio)
        bucket["by_subject"][subject].append(ratio)
        bucket["subjects"].add((subject, subject_name))
        if len(bucket["ids"]) < 20:
            bucket["ids"].append(attempt.pk)
    return stats


def _task_key(learner_id, rule_id, competency_id):
    """Null-safe in-memory key: a missing competency uses the 0 sentinel."""
    return (learner_id, rule_id or 0, competency_id or 0)


def _require_institution(institution):
    if institution is None or getattr(institution, "pk", None) is None:
        raise ValueError("This operation needs a saved institution.")
    return institution


def remediation_summary(institution):
    """Count current remediation tasks by status; used by the API and snapshots."""
    _require_institution(institution)
    tasks = RemediationTask.objects.filter(institution=institution)
    return {
        "total": tasks.count(),
        "by_status": {
            value: tasks.filter(status=value).count()
            for value, _label in RemediationTask.STATUSES
        },
        "active_rules": RemediationRule.objects.filter(
            institution=institution, is_active=True
        ).count(),
    }


@transaction.atomic
def evaluate_remediation(institution):
    """Evaluate active rules once and return created/updated/skipped counts.

    The same learner/rule/competency combination always maps to one task.
    Completed and dismissed tasks are never re-opened or overwritten.
    """
    _require_institution(institution)
    rules = list(
        RemediationRule.objects.filter(institution=institution, is_active=True)
        .select_related("competency")
    )
    summary = {
        "rules_evaluated": len(rules),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "tasks_touched": 0,
    }
    if not rules:
        return summary

    result_stats = _learner_result_stats(institution)
    evidence_cache = {}
    existing = {}
    for task in RemediationTask.objects.filter(
        institution=institution, rule_id__in=[rule.pk for rule in rules]
    ):
        existing[_task_key(task.learner_id, task.rule_id, task.competency_id)] = task

    evaluated_at = timezone.now().isoformat()
    for rule in rules:
        competency_id = getattr(rule, "competency_id", None)
        if competency_id not in evidence_cache:
            evidence_cache[competency_id] = _learner_evidence_stats(
                institution, competency_id=competency_id
            )
        evidence_stats = evidence_cache[competency_id]
        threshold = _decimal(rule.mastery_below)
        if threshold is None:
            threshold = ZERO
        try:
            min_attempts = max(1, int(getattr(rule, "min_attempts", 1) or 1))
        except (TypeError, ValueError):
            min_attempts = 1

        for learner_id in sorted(set(evidence_stats) | set(result_stats)):
            signals = {}
            evidence = evidence_stats.get(learner_id)
            if evidence and evidence["attempts"] >= min_attempts:
                average = _average(evidence["scores"])
                if average is not None and average < threshold:
                    signals["competency_evidence"] = {
                        "attempts": evidence["attempts"],
                        "average_mastery": _number(average),
                        "levels": dict(evidence["levels"]),
                        "evidence_ids": evidence["ids"],
                    }
            results = result_stats.get(learner_id)
            if results and results["attempts"] >= min_attempts:
                average = _average(results["ratios"])
                if average is not None and average < threshold:
                    signals["results"] = {
                        "attempts": results["attempts"],
                        "average_ratio": _number(average),
                        "result_ids": results["ids"],
                    }
            if not signals:
                continue

            key = _task_key(learner_id, rule.pk, competency_id)
            task = existing.get(key)
            if task is not None and task.status in CLOSED_STATUSES:
                summary["skipped"] += 1
                continue

            evidence_payload = {
                "rule": {
                    "id": rule.pk,
                    "reference": getattr(rule, "reference", ""),
                    "name": rule.name,
                    "action": rule.action,
                },
                "threshold": {
                    "mastery_below": str(threshold),
                    "min_attempts": min_attempts,
                },
                "competency_id": competency_id,
                "signals": signals,
                "evaluated_at": evaluated_at,
            }
            if task is None:
                task = RemediationTask(
                    institution=institution,
                    learner_id=learner_id,
                    rule=rule,
                    competency_id=competency_id,
                    status=RemediationTask.OPEN,
                    evidence=evidence_payload,
                )
                task.save()
                existing[key] = task
                summary["created"] += 1
            else:
                task.evidence = evidence_payload
                task.save()
                summary["updated"] += 1
            summary["tasks_touched"] += 1
    return summary


def build_cohorts(institution, filters=None):
    """Group real learners by school class and subject; never write records.

    Supported filters: ``class_room_id``/``school_class_id``, ``subject_id``,
    ``status`` and ``term_id``. Subjects come from exam/quiz result records;
    learners without either are reported under "Unassigned".
    """
    _require_institution(institution)
    filters = filters or {}
    learners = Learner.objects.filter(institution=institution).select_related("class_room")
    class_id = _positive_id(filters.get("class_room_id", filters.get("school_class_id")))
    subject_id = _positive_id(filters.get("subject_id"))
    term_id = _positive_id(filters.get("term_id"))
    status = filters.get("status")
    if class_id is not None:
        learners = learners.filter(class_room_id=class_id)
    if status:
        learners = learners.filter(status=status)
    learners = list(learners)
    if not learners:
        return []
    learner_ids = [learner.pk for learner in learners]

    evidence = _learner_evidence_stats(institution, learner_ids=learner_ids)
    attendance = defaultdict(lambda: {"present": 0, "total": 0})
    attendance_rows = AttendanceRecord.objects.filter(
        institution=institution, learner_id__in=learner_ids
    )
    if term_id is not None:
        attendance_rows = attendance_rows.filter(term_id=term_id)
    for row in attendance_rows:
        bucket = attendance[row.learner_id]
        bucket["total"] += 1
        if getattr(row, "status", None) == AttendanceStatus.PRESENT:
            bucket["present"] += 1

    results = _learner_result_stats(
        institution, learner_ids=learner_ids, subject_id=subject_id, term_id=term_id
    )
    class_labels = {
        learner.pk: (
            learner.class_room_id,
            getattr(learner.class_room, "display_name", None) or "Unassigned",
        )
        for learner in learners
    }
    learner_subjects = {}
    for learner in learners:
        stats = results.get(learner.pk)
        subjects = set(stats["subjects"]) if stats else set()
        learner_subjects[learner.pk] = subjects or {(None, "Unassigned")}

    grouped = defaultdict(set)
    for learner in learners:
        class_key = class_labels[learner.pk]
        for subject_key, subject_label in learner_subjects[learner.pk]:
            if subject_id is not None and subject_key != subject_id:
                continue
            grouped[(class_key[0], class_key[1], subject_key, subject_label)].add(learner.pk)

    rows = []
    for (class_key, class_label, subject_key, subject_label), ids in sorted(
        grouped.items(), key=lambda item: (item[0][1], item[0][3])
    ):
        mastery = []
        evidence_records = 0
        for learner_id in ids:
            bucket = evidence.get(learner_id)
            if not bucket:
                continue
            evidence_records += bucket["attempts"]
            if bucket["scores"]:
                mastery.append(_average(bucket["scores"]))
        average_mastery = _average(mastery)

        present = sum(attendance.get(learner_id, {}).get("present", 0) for learner_id in ids)
        total_attendance = sum(attendance.get(learner_id, {}).get("total", 0) for learner_id in ids)
        ratios = []
        result_records = 0
        for learner_id in ids:
            bucket = results.get(learner_id)
            if not bucket:
                continue
            matches = bucket["by_subject"].get(subject_key, [])
            ratios.extend(matches)
            result_records += len(matches)
        average_result = _average(ratios)

        rows.append({
            "class": class_label,
            "class_room_id": class_key,
            "subject": subject_label,
            "subject_id": subject_key,
            "learners": len(ids),
            "average_mastery": _number(average_mastery * HUNDRED) if average_mastery is not None else None,
            "attendance_percentage": (
                round(present / total_attendance * 100, 1) if total_attendance else None
            ),
            "result_average": (
                _number(average_result * HUNDRED) if average_result is not None else None
            ),
            "evidence_records": evidence_records,
            "attendance_records": total_attendance,
            "result_records": result_records,
        })
    return rows


def dashboard_metrics(institution):
    """Scoped KPIs built only from records belonging to ``institution``."""
    _require_institution(institution)
    learners = Learner.objects.filter(institution=institution)
    attendance = AttendanceRecord.objects.filter(institution=institution)
    results = ExamResult.objects.filter(institution=institution).select_related("exam")
    evidence = CompetencyEvidence.objects.filter(institution=institution).select_related("rubric_level")

    total_attendance = attendance.count()
    present = attendance.filter(status=AttendanceStatus.PRESENT).count()
    average_score = results.aggregate(average=Avg("score"))["average"]
    mastery = [
        score for item in evidence if (score := _mastery_from_evidence(item)) is not None
    ]
    return {
        "scope": {"institution_id": institution.pk, "institution": getattr(institution, "name", "")},
        "total_learners": learners.count(),
        "active_learners": learners.filter(status="ACTIVE").count(),
        "attendance_records": total_attendance,
        "attendance_rate_percent": (
            round(present / total_attendance * 100, 1) if total_attendance else None
        ),
        "attendance_breakdown": {
            item["status"]: item["value"] for item in attendance_status_series(attendance)
        },
        "exam_results_recorded": results.count(),
        "average_exam_score": _number(average_score),
        "competency_evidence_records": evidence.count(),
        "average_mastery_percent": (
            _number(_average(mastery) * HUNDRED) if mastery else None
        ),
        "open_remediation_tasks": RemediationTask.objects.filter(
            institution=institution, status=RemediationTask.OPEN
        ).count(),
    }


@transaction.atomic
def refresh_snapshot(institution, dataset, period, user=None):
    """Compute and upsert one snapshot for an institution and period."""
    _require_institution(institution)
    valid = dict(AnalyticsSnapshot.DATASETS)
    if dataset not in valid:
        raise ValueError(f"Unknown dataset {dataset!r}. Choose one of: {', '.join(valid)}.")
    if not period or not str(period).strip():
        raise ValueError("A period is required, for example '2026-Term-1'.")

    if dataset == AnalyticsSnapshot.DASHBOARD:
        payload = dashboard_metrics(institution)
    elif dataset == AnalyticsSnapshot.COHORTS:
        payload = {
            "scope": {"institution_id": institution.pk, "institution": getattr(institution, "name", "")},
            "cohorts": build_cohorts(institution),
        }
    elif dataset == AnalyticsSnapshot.ATTENDANCE:
        attendance = AttendanceRecord.objects.filter(institution=institution)
        total = attendance.count()
        present = attendance.filter(status=AttendanceStatus.PRESENT).count()
        payload = {
            "scope": {"institution_id": institution.pk, "institution": getattr(institution, "name", "")},
            "attendance_records": total,
            "attendance_rate_percent": round(present / total * 100, 1) if total else None,
            "status_breakdown": {
                item["status"]: item["value"] for item in attendance_status_series(attendance)
            },
        }
    elif dataset == AnalyticsSnapshot.ASSESSMENTS:
        results = ExamResult.objects.filter(institution=institution).select_related("exam")
        average_score = results.aggregate(average=Avg("score"))["average"]
        payload = {
            "scope": {"institution_id": institution.pk, "institution": getattr(institution, "name", "")},
            "exam_results_recorded": results.count(),
            "average_exam_score": _number(average_score),
            "recent_results": exam_series(results)[-20:],
        }
    else:
        evaluation = evaluate_remediation(institution)
        payload = remediation_summary(institution)
        payload["evaluation"] = evaluation

    payload["dataset"] = dataset
    payload["period"] = period
    snapshot, _created = AnalyticsSnapshot.objects.update_or_create(
        institution=institution,
        dataset=dataset,
        period=period,
        defaults={
            "payload": payload,
            "generated_by": user,
            "generated_at": timezone.now(),
        },
    )
    return snapshot
