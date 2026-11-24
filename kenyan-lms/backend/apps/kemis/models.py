"""Local KEMIS-style export staging models.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel, TimeStampedModel

# Shared choices. ``apps.core.codes`` already allocates KEM- and KFM-prefixed
# references for the two models below, so no extra reference logic lives here.
DATASET_CHOICES = [
    ("LEARNERS", "Learners"),
    ("TEACHERS", "Teachers"),
    ("INSTITUTION", "Institution"),
    ("ENROLLMENT", "Enrollment"),
    ("ATTENDANCE", "Attendance"),
    ("RESULTS", "Results"),
]
FORMAT_CHOICES = [("CSV", "CSV"), ("JSON", "JSON")]
STATUS_CHOICES = [("QUEUED", "Queued"), ("READY", "Ready"), ("FAILED", "Failed")]


class KemisExport(AutoReferenceModelMixin, InstitutionScopedModel):
    """One staged export job and its generated output (never transmitted)."""

    reference = models.CharField(max_length=50, blank=True, unique=True)
    dataset = models.CharField(max_length=20, choices=DATASET_CHOICES, db_index=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default="CSV")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="QUEUED", db_index=True)
    filters = models.JSONField(default=dict, blank=True)
    record_count = models.PositiveIntegerField(default=0)
    generated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="kemis_exports",
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    payload = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["institution", "dataset", "status"])]

    def __str__(self):
        return f"{self.reference or self.pk} ({self.dataset}/{self.format})"


class KemisFieldMapping(AutoReferenceModelMixin, TimeStampedModel):
    """Platform-wide, local column mapping table (not institution scoped)."""

    reference = models.CharField(max_length=50, blank=True, unique=True)
    dataset = models.CharField(max_length=20, choices=DATASET_CHOICES, db_index=True)
    source_field = models.CharField(
        max_length=150,
        help_text="Dotted attribute path on a source record, e.g. user.full_name.",
    )
    target_column = models.CharField(max_length=150)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["dataset", "ordering"]

    def __str__(self):
        return f"{self.dataset}: {self.source_field} -> {self.target_column}"
