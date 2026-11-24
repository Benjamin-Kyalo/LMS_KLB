"""KICD-style internal review workflow; this does not submit anything to KICD and does not represent official KICD approval."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class ApprovalRequest(AutoReferenceModelMixin, InstitutionScopedModel):
    """An internal review record for a piece of curriculum content."""

    CONTENT_TYPES = [
        ("TEXTBOOK", "Textbook"),
        ("CHAPTER", "Chapter"),
        ("RESOURCE", "Learning resource"),
        ("COURSE", "Course"),
        ("OTHER", "Other"),
    ]

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CHANGES_REQUESTED", "Changes requested"),
        ("PUBLISHED", "Published"),
    ]

    SUBMITTABLE_STATUSES = {"DRAFT", "REJECTED", "CHANGES_REQUESTED"}
    REVIEWABLE_STATUSES = {"SUBMITTED", "UNDER_REVIEW"}

    reference = models.CharField(max_length=50, blank=True, unique=True)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default="OTHER", db_index=True)
    textbook = models.ForeignKey(
        "content.DigitalTextbook", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approval_requests",
    )
    content_resource = models.ForeignKey(
        "content.ContentResource", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approval_requests",
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="DRAFT", db_index=True)
    submitted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approval_submissions",
    )
    reviewed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approval_reviews",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    # Optional external authority reference recorded by a user; the system
    # never contacts KICD or claims that this value is official.
    kicd_reference = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["institution", "status"])]

    def __str__(self):
        return f"{self.reference or self.pk} - {self.title}"


class ApprovalDecision(AutoReferenceModelMixin, InstitutionScopedModel):
    """One decision recorded against an approval request."""

    DECISIONS = [
        ("APPROVE", "Approve"),
        ("REJECT", "Reject"),
        ("REQUEST_CHANGES", "Request changes"),
    ]

    RESULTING_STATUS = {
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
        "REQUEST_CHANGES": "CHANGES_REQUESTED",
    }

    reference = models.CharField(max_length=50, blank=True, unique=True)
    request = models.ForeignKey(
        ApprovalRequest, on_delete=models.CASCADE, related_name="decisions",
    )
    decision = models.CharField(max_length=20, choices=DECISIONS)
    notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approval_decisions",
    )
    decided_at = models.DateTimeField(auto_now_add=True)
    reference_to_source = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-decided_at", "-id"]

    def __str__(self):
        return f"{self.reference or self.pk} - {self.get_decision_display()}"


class ApprovalChecklistItem(AutoReferenceModelMixin, InstitutionScopedModel):
    """A completeness check that must be met before a request is submitted."""

    reference = models.CharField(max_length=50, blank=True, unique=True)
    request = models.ForeignKey(
        ApprovalRequest, on_delete=models.CASCADE, related_name="checklist",
    )
    label = models.CharField(max_length=200)
    is_met = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label
