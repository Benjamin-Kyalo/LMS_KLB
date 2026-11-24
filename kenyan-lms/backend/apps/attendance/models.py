"""Daily attendance records."""
from django.db import models

from apps.core.constants import AttendanceStatus
from apps.core.models import InstitutionScopedModel


class AttendanceRecord(InstitutionScopedModel):
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="attendance_records")
    school_class = models.ForeignKey("institutions.SchoolClass", on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey("institutions.Term", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=AttendanceStatus.CHOICES, default=AttendanceStatus.PRESENT)
    marked_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "learner"]
        constraints = [
            models.UniqueConstraint(fields=["learner", "date"], name="one_attendance_per_learner_per_day")
        ]
        indexes = [models.Index(fields=["institution", "date", "status"])]
