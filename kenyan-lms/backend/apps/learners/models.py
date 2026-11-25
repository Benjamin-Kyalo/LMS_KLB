"""Learner records, guardians and transfer history."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class Learner(AutoReferenceModelMixin, InstitutionScopedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="learner_profile")
    admission_number = models.CharField(max_length=50)
    assessment_number = models.CharField(max_length=50, blank=True, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    class_room = models.ForeignKey(
        "institutions.SchoolClass", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="learners",
    )
    status = models.CharField(
        max_length=20, default="ACTIVE",
        choices=[("ACTIVE", "Active"), ("TRANSFERRED", "Transferred"), ("ALUMNI", "Alumni"), ("SUSPENDED", "Suspended")],
        db_index=True,
    )
    date_admitted = models.DateField(null=True, blank=True)
    date_left = models.DateField(null=True, blank=True)
    previous_school = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["admission_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "admission_number"], name="unique_admission_per_institution"
            )
        ]
        indexes = [models.Index(fields=["institution", "class_room", "status"])]

    def __str__(self):
        return f"{self.user.full_name} ({self.admission_number})"


class LearnerGuardian(models.Model):
    """Links a guardian to a learner with explicit access permissions."""

    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="guardian_links")
    guardian = models.ForeignKey("guardians.Guardian", on_delete=models.CASCADE, related_name="learner_links")
    relationship = models.CharField(max_length=50, blank=True)
    # Admin-created links and links produced by the verification workflow are
    # trusted; a request that is still pending never creates this record.
    is_verified = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    can_view_academics = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    can_view_fees = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["learner", "guardian"], name="unique_learner_guardian")
        ]

    def __str__(self):
        return f"{self.guardian.user.full_name} -> {self.learner.user.full_name}"


class GuardianLinkRequest(AutoReferenceModelMixin, InstitutionScopedModel):
    """A guardian's proposed learner link, pending administrative verification."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    ]

    guardian = models.ForeignKey(
        "guardians.Guardian", on_delete=models.CASCADE, related_name="link_requests"
    )
    learner = models.ForeignKey(
        Learner, on_delete=models.CASCADE, related_name="guardian_link_requests"
    )
    learner_identifier = models.CharField(max_length=50)
    reference = models.CharField(max_length=50, blank=True, unique=True)
    relationship = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    notes = models.TextField(blank=True)
    verified_link = models.ForeignKey(
        LearnerGuardian, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verified_requests",
    )
    decided_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="guardian_link_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["guardian", "learner"],
                name="unique_pending_guardian_link_request",
                condition=models.Q(status="PENDING"),
            )
        ]

    def __str__(self):
        return f"{self.guardian.user.full_name} -> {self.learner.user.full_name} ({self.status})"


class TransferRecord(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="transfers")
    from_institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="outgoing_transfers"
    )
    to_institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, related_name="incoming_transfers",
        null=True, blank=True,
    )
    transfer_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, default="PENDING",
        choices=[("PENDING", "Pending"), ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled")],
    )
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transfer_date"]
