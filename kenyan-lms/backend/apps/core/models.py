"""Abstract base models and the audit log."""
from django.db import models

from apps.core.constants import Roles


class AutoReferenceModelMixin:
    """Fill blank business codes automatically on every save path."""

    def save(self, *args, **kwargs):
        from apps.core.codes import ensure_reference
        ensure_reference(self)
        return super().save(*args, **kwargs)


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps to any model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InstitutionScopedModel(TimeStampedModel):
    """
    Base for records that belong to one institution.

    The ``institution`` field is the backbone of data isolation: every
    list view filters on it, so no user can see another school's records.
    """

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
    )

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """Records important actions. Never delete audit rows."""

    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=50, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entity_type", "entity_id"])]

    def __str__(self):
        return f"{self.action} on {self.entity_type} by {self.user}"
