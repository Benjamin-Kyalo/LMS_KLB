"""Parent and guardian profiles."""
from django.db import models

from apps.core.models import InstitutionScopedModel


class Guardian(InstitutionScopedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="guardian_profile")
    phone = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    relationship_to_learner = models.CharField(max_length=50, blank=True)
    preferred_language = models.CharField(max_length=10, default="en")
    receive_sms = models.BooleanField(default=True)

    def __str__(self):
        return self.user.full_name
