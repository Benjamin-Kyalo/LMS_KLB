"""Chart-ready analytics built from live institutional records."""
from collections import Counter
from datetime import timedelta

from django.db.models import Avg, Count

from apps.assessments.models import ExamResult
from apps.attendance.models import AttendanceRecord
from apps.courses.models import LessonProgress
from apps.core.constants import AttendanceStatus, MasteryLevel, Roles
from apps.curriculum.models import CompetencyEvidence
from apps.learners.models import Learner
from apps.reports.scoping import scoped_institution_id

LEARNER_STATUSES = [
    ("ACTIVE", "Active"),
    ("TRANSFERRED", "Transferred"),
    ("ALUMNI", "Alumni"),
    ("SUSPENDED", "Suspended"),
]
PROGRESS_STATUSES = [
    ("NOT_STARTED", "Not started"),
    ("IN_PROGRESS", "In progress"),
    ("COMPLETED", "Completed"),
]


def _scoped(model, institution_id):
    queryset = model.objects.all()
    if institution_id:
        return queryset.filter(institution_id=institution_id)
    return queryset.none() if institution_id == 0 else queryset


def _number(value):
    return None if value is None else round(float(value), 1)


def attendance_status_series(attendance):
    counts = Counter(attendance.values_list("status", flat=True))
    return [
        {"status": value, "label": label, "value": counts.get(value, 0)}
        for value, label in AttendanceStatus.CHOICES
    ]


def attendance_trend_series(attendance, days=14):
    """Return the last ``days`` dated attendance rows in chronological order."""
    rows = list(
        attendance.order_by("-date")
        .values("date")
        .annotate(total=Count("id"))
        .values_list("date", flat=True)[:days]
    )
    dates = sorted(rows)
    if not dates:
        return []
    start = dates[0]
    end = dates[-1]
    by_date = {
        (date, status): count
        for date, status, count in attendance.filter(date__range=(start, end))
        .values_list("date", "status")
        .annotate(count=Count("id"))
    }
    series = []
    current = start
    while current <= end:
        item = {"date": current.isoformat()}
        for status, _ in AttendanceStatus.CHOICES:
            item[status] = by_date.get((current, status), 0)
        series.append(item)
        current += timedelta(days=1)
    return series[-days:]


def exam_series(results):
    return [
        {
            "label": result.exam.title,
            "date": result.exam.exam_date.isoformat() if result.exam.exam_date else None,
            "score": float(result.score),
            "max_score": float(result.exam.max_score),
            "percentage": round(float(result.score) / float(result.exam.max_score) * 100, 1)
            if result.exam.max_score else None,
        }
        for result in results.select_related("exam").order_by("exam__exam_date", "id")
    ]


def class_performance_series(learners, results):
    rows = (
        results.values("learner__class_room__name")
        .annotate(average=Avg("score"), results=Count("id"))
        .order_by("learner__class_room__name")
    )
    by_class = {
        (row["learner__class_room__name"] or "Unassigned"): {
            "class": row["learner__class_room__name"] or "Unassigned",
            "average_score": _number(row["average"]),
            "results": row["results"],
        }
        for row in rows
    }
    for name, count in learners.values("class_room__name").annotate(total=Count("id")):
        key = name or "Unassigned"
        by_class.setdefault(key, {"class": key, "average_score": None, "results": 0})
        by_class[key]["learners"] = count
    for item in by_class.values():
        item.setdefault("learners", 0)
    return sorted(by_class.values(), key=lambda row: row["class"])


def build_analytics(user):
    """Return one JSON-serialisable object that powers every dashboard chart."""
    institution_id = scoped_institution_id(user)
    learners = _scoped(Learner, institution_id)
    attendance = _scoped(AttendanceRecord, institution_id)
    results = _scoped(ExamResult, institution_id)
    progress = _scoped(LessonProgress, institution_id)
    evidence = _scoped(CompetencyEvidence, institution_id)

    learner_counts = Counter(learners.values_list("status", flat=True))
    progress_counts = Counter(progress.values_list("status", flat=True))
    evidence_counts = Counter(evidence.values_list("achieved_level", flat=True))

    return {
        "scope": {
            "institution_id": None if institution_id is None or institution_id == 0 else institution_id,
            "platform_wide": institution_id is None,
            "empty_scope": institution_id == 0,
        },
        "attendance_status": attendance_status_series(attendance),
        "attendance_trend": attendance_trend_series(attendance),
        "exam_results": exam_series(results)[-20:],
        "performance_by_class": class_performance_series(learners, results),
        "learner_status": [
            {"status": value, "label": label, "value": learner_counts.get(value, 0)}
            for value, label in LEARNER_STATUSES
        ],
        "course_progress": [
            {"status": value, "label": label, "value": progress_counts.get(value, 0)}
            for value, label in PROGRESS_STATUSES
        ],
        "competency_levels": [
            {"level": value, "label": label, "value": evidence_counts.get(value, 0)}
            for value, label in MasteryLevel.CHOICES
        ],
    }
