"""Dashboard, analytics and saved report endpoints."""
from django.db.models import Avg
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assessments.models import ExamResult
from apps.attendance.models import AttendanceRecord
from apps.core.constants import Roles
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.learners.models import Learner
from apps.reports.analytics import (
    attendance_status_series,
    build_analytics,
    exam_series,
)
from apps.reports.models import ReportSnapshot
from apps.reports.scoping import (
    can_view_learner,
    dashboard_viewer,
    guardian_link,
    scoped_institution_id,
)
from apps.reports.serializers import ReportSnapshotSerializer


def _require_dashboard_viewer(user):
    if not dashboard_viewer(user):
        raise PermissionDenied("This summary is available to school staff only.")


def _scoped_queryset(model, institution_id):
    queryset = model.objects.all()
    if institution_id:
        return queryset.filter(institution_id=institution_id)
    return queryset.none() if institution_id == 0 else queryset


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def school_dashboard(request):
    """One useful number per card, each traceable to real records."""
    _require_dashboard_viewer(request.user)
    institution_id = scoped_institution_id(request.user)
    learners = _scoped_queryset(Learner, institution_id)
    attendance = _scoped_queryset(AttendanceRecord, institution_id)
    results = _scoped_queryset(ExamResult, institution_id)

    total_attendance = attendance.count()
    present = attendance.filter(status="PRESENT").count()
    average_score = results.aggregate(average=Avg("score"))["average"]
    return Response({
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
        "average_exam_score": round(average_score, 1) if average_score is not None else None,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics(request):
    """Chart-ready attendance, performance and progress data."""
    _require_dashboard_viewer(request.user)
    return Response(build_analytics(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_learners(request):
    """Learners the signed-in user is allowed to open, for report pickers."""
    user = request.user
    if dashboard_viewer(user):
        learners = _scoped_queryset(Learner, scoped_institution_id(user))
    elif user.role == Roles.LEARNER:
        learners = Learner.objects.filter(user=user)
    elif user.role == Roles.GUARDIAN:
        learners = Learner.objects.filter(guardian_links__guardian__user=user)
    else:
        learners = Learner.objects.none()
    return Response([
        {
            "id": learner.id,
            "learner_name": learner.user.full_name,
            "admission_number": learner.admission_number,
        }
        for learner in learners.select_related("user").order_by("user__first_name", "user__last_name")
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learner_report(request, learner_id):
    """Individual learner summary with linked detail counts."""
    try:
        learner = Learner.objects.select_related("user", "institution", "class_room").get(pk=learner_id)
    except Learner.DoesNotExist:
        return Response({"detail": "Learner not found."}, status=404)

    if not can_view_learner(request.user, learner):
        return Response({"detail": "You cannot access this learner's records."}, status=403)

    link = guardian_link(request.user, learner)
    attendance = AttendanceRecord.objects.filter(learner=learner)
    results = ExamResult.objects.filter(learner=learner).select_related("exam")
    can_see_attendance = not link or link.can_view_attendance
    can_see_academics = not link or link.can_view_academics

    average = results.aggregate(avg=Avg("score"))["avg"] if can_see_academics else None
    return Response({
        "learner": {
            "id": learner.id,
            "name": learner.user.full_name,
            "admission_number": learner.admission_number,
            "class": learner.class_room.name if learner.class_room else None,
            "institution": learner.institution.name,
        },
        "attendance": (
            {item["status"]: item["value"] for item in attendance_status_series(attendance)}
            if can_see_attendance else {}
        ),
        "exams": exam_series(results) if can_see_academics else [],
        "average_score": round(float(average), 1) if average is not None else None,
        "permissions": {
            "attendance": can_see_attendance,
            "academics": can_see_academics,
        },
    })


class ReportSnapshotViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ReportSnapshot.objects.select_related("generated_by")
    serializer_class = ReportSnapshotSerializer
    filterset_fields = ["report_type"]

    def perform_create(self, serializer):
        if not self.request.user.institution_id:
            raise ValidationError(
                "A saved report needs an institution. Use a school account, or "
                "choose an institution before saving as a platform administrator."
            )
        serializer.save(
            institution=self.request.user.institution,
            generated_by=self.request.user,
        )
