"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from decimal import Decimal

from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel, TimeStampedModel  # noqa: F401


class AnalyticsSnapshot(AutoReferenceModelMixin, InstitutionScopedModel):
    """A computed, locally stored payload for one dataset and period."""

    DASHBOARD = "DASHBOARD"
    COHORTS = "COHORTS"
    ATTENDANCE = "ATTENDANCE"
    ASSESSMENTS = "ASSESSMENTS"
    REMEDIATION = "REMEDIATION"
    DATASETS = [
        (DASHBOARD, "Dashboard KPIs"),
        (COHORTS, "Class and subject cohorts"),
        (ATTENDANCE, "Attendance summary"),
        (ASSESSMENTS, "Assessment summary"),
        (REMEDIATION, "Remediation summary"),
    ]

    reference = models.CharField(max_length=50, blank=True, unique=True)
    dataset = models.CharField(max_length=20, choices=DATASETS)
    period = models.CharField(max_length=50, help_text='For example "2026-Term-1".')
    payload = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="analytics_snapshots",
    )
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-generated_at", "-created_at"]
        unique_together = (("institution", "dataset", "period"),)

    def __str__(self):
        return f"{self.get_dataset_display()} - {self.period}"


class RemediationRule(AutoReferenceModelMixin, InstitutionScopedModel):
    """A school's rule for flagging learners whose observed mastery is low."""

    PRACTICE = "PRACTICE"
    RESOURCE = "RESOURCE"
    COURSE = "COURSE"
    TEACHER_REVIEW = "TEACHER_REVIEW"
    ACTIONS = [
        (PRACTICE, "Targeted practice"),
        (RESOURCE, "Recommended resource"),
        (COURSE, "Recommended course"),
        (TEACHER_REVIEW, "Teacher review"),
    ]

    reference = models.CharField(max_length=50, blank=True, unique=True)
    name = models.CharField(max_length=200)
    competency = models.ForeignKey(
        "curriculum.Competency", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="remediation_rules",
    )
    mastery_below = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.50"),
        help_text="Threshold on a 0-1 scale (0.50 means 50%).",
    )
    min_attempts = models.PositiveIntegerField(default=1)
    action = models.CharField(max_length=20, choices=ACTIONS, default="PRACTICE")
    target_resource = models.ForeignKey(
        "content.ContentResource", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="remediation_rules",
    )
    target_course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="remediation_rules",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["institution", "is_active"])]

    def __str__(self):
        return self.name


class RemediationTask(AutoReferenceModelMixin, InstitutionScopedModel):
    """One learner/rule flag. The engine updates these idempotently."""

    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    DISMISSED = "DISMISSED"
    STATUSES = [
        (OPEN, "Open"),
        (ASSIGNED, "Assigned"),
        (COMPLETED, "Completed"),
        (DISMISSED, "Dismissed"),
    ]

    reference = models.CharField(max_length=50, blank=True, unique=True)
    learner = models.ForeignKey(
        "learners.Learner", on_delete=models.CASCADE, related_name="remediation_tasks",
    )
    rule = models.ForeignKey(
        RemediationRule, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="remediation_tasks",
    )
    competency = models.ForeignKey(
        "curriculum.Competency", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="remediation_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUSES, default="OPEN", db_index=True)
    evidence = models.JSONField(default=dict, blank=True)
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_remediation_tasks",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = (("learner", "rule", "competency"),)
        indexes = [models.Index(fields=["institution", "status"])]

    def __str__(self):
        return f"{self.reference or self.pk} - {self.get_status_display()}"
