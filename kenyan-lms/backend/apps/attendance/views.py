"""Attendance endpoints, including bulk marking."""
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.attendance.models import AttendanceRecord
from apps.attendance.serializers import AttendanceRecordSerializer, BulkAttendanceSerializer
from apps.core.constants import Capabilities
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.learners.scoping import FamilyScopedReadMixin


class AttendanceRecordViewSet(
    FamilyScopedReadMixin, StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    capability = Capabilities.ATTENDANCE_MANAGE
    queryset = AttendanceRecord.objects.select_related("learner__user", "school_class")
    serializer_class = AttendanceRecordSerializer
    filterset_fields = ["learner", "school_class", "term", "date", "status"]
    learner_path = "learner"
    guardian_permission = "can_view_attendance"

    def perform_create(self, serializer):
        # Use the shared scoping helper so institution is never missing and
        # cannot be smuggled in by the client.
        if not self.request.user.institution_id:
            raise ValidationError("Choose an institution before recording attendance.")
        self._scoped_save(serializer, marked_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_mark(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        created = []
        with transaction.atomic():
            for item in data["records"]:
                record, _ = AttendanceRecord.objects.update_or_create(
                    learner_id=item["learner"],
                    date=data["date"],
                    defaults={
                        "institution": request.user.institution,
                        "school_class_id": data["school_class"],
                        "term_id": data.get("term"),
                        "status": item["status"],
                        "marked_by": request.user,
                        "notes": item.get("notes", ""),
                    },
                )
                created.append(record)
        return Response({"saved": len(created)}, status=status.HTTP_201_CREATED)
