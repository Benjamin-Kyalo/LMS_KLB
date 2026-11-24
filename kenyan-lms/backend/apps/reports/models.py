"""Saved report snapshots. Live dashboards are computed, not stored."""
from django.db import models

from apps.core.models import InstitutionScopedModel


class ReportSnapshot(InstitutionScopedModel):
    REPORT_TYPES = [
        ("ATTENDANCE", "Attendance summary"),
        ("PERFORMANCE", "Academic performance"),
        ("COMPETENCY", "Competency progression"),
        ("LEARNER", "Individual learner report"),
        ("CLASS", "Class report"),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    period_label = models.CharField(max_length=100, blank=True)
    data = models.JSONField(default=dict)
    generated_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
