"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from django.db import models

from apps.core.models import InstitutionScopedModel, TimeStampedModel, AutoReferenceModelMixin


class TutorConversation(AutoReferenceModelMixin, InstitutionScopedModel):
    """One tutoring thread, optionally linked to a learner in the same school."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    reference = models.CharField(max_length=50, blank=True, unique=True)
    title = models.CharField(max_length=200)
    learner = models.ForeignKey(
        "learners.Learner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tutor_conversations",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    started_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tutor_conversations_started",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["institution", "status"])]

    def __str__(self):
        return f"{self.reference or 'TUT'}: {self.title}"


class TutorMessage(AutoReferenceModelMixin, InstitutionScopedModel):
    """A single user question or grounded tutor reply in a conversation."""

    class Role(models.TextChoices):
        USER = "USER", "Learner"
        TUTOR = "TUTOR", "Tutor"

    reference = models.CharField(max_length=50, blank=True, unique=True)
    conversation = models.ForeignKey(
        TutorConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER, db_index=True)
    body = models.TextField()
    # Simple, serialisable records: {"kind": ..., "code": ..., "label": ...}.
    sources = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tutor_messages",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["institution", "conversation", "created_at"])]

    def __str__(self):
        return f"{self.reference or 'TMSG'}: {self.role}"
