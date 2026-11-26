"""Parent and guardian profiles."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class Guardian(AutoReferenceModelMixin, InstitutionScopedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="guardian_profile")
    guardian_number = models.CharField(max_length=50, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    relationship_to_learner = models.CharField(max_length=50, blank=True)
    preferred_language = models.CharField(max_length=10, default="en")
    receive_sms = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "guardian_number"],
                condition=models.Q(guardian_number__gt=""),
                name="unique_guardian_number_per_institution",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.guardian_number})"
