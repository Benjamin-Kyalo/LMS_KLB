"""Digital textbooks, chapters and linked learning resources."""
from django.db import models

from apps.core.constants import ContentStatus
from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel, TimeStampedModel


class Publisher(AutoReferenceModelMixin, TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DigitalTextbook(AutoReferenceModelMixin, TimeStampedModel):
    """A title in the catalogue. Access is controlled separately per institution."""

    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="textbooks")
    title = models.CharField(max_length=250)
    subtitle = models.CharField(max_length=250, blank=True)
    isbn = models.CharField(max_length=30, blank=True, db_index=True)
    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    education_level = models.ForeignKey("curriculum.EducationLevel", on_delete=models.SET_NULL, null=True, blank=True)
    curriculum_framework = models.ForeignKey("curriculum.CurriculumFramework", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="content/covers/", null=True, blank=True)
    license_type = models.CharField(
        max_length=30, default="INSTITUTION",
        choices=[("OPEN", "Open"), ("INSTITUTION", "Institution licence"), ("PER_LEARNER", "Per learner"), ("EXPIRED", "Expired")],
    )
    status = models.CharField(max_length=20, choices=ContentStatus.CHOICES, default=ContentStatus.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["status", "subject", "education_level"])]

    def __str__(self):
        return self.title


class Chapter(AutoReferenceModelMixin, TimeStampedModel):
    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    chapter_number = models.PositiveSmallIntegerField(default=1)
    content = models.TextField(blank=True)
    learning_outcome = models.ForeignKey("curriculum.LearningOutcome", on_delete=models.SET_NULL, null=True, blank=True)
    is_downloadable = models.BooleanField(default=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["textbook", "sequence", "chapter_number"]
        constraints = [
            models.UniqueConstraint(fields=["textbook", "chapter_number"], name="unique_chapter_number")
        ]

    def __str__(self):
        return f"{self.textbook.title} - {self.title}"


class ContentResource(TimeStampedModel):
    """Audio, video, PDF or interactive linked to a chapter or standalone."""

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name="resources")
    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, null=True, blank=True, related_name="resources")
    title = models.CharField(max_length=200)
    resource_type = models.CharField(
        max_length=20, default="PDF",
        choices=[("PDF", "PDF"), ("VIDEO", "Video"), ("AUDIO", "Audio"), ("IMAGE", "Image"), ("INTERACTIVE", "Interactive"), ("LINK", "External link")],
    )
    file = models.FileField(upload_to="content/resources/", null=True, blank=True)
    external_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    offline_available = models.BooleanField(default=False)
    size_kb = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["title"]


class Exercise(TimeStampedModel):
    """An exercise attached to a chapter. Questions are stored as JSON for flexibility."""

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="exercises")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    questions = models.JSONField(default=list)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["chapter", "sequence"]


class ExerciseAttempt(InstitutionScopedModel):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="exercise_attempts")
    answers = models.JSONField(default=list)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [models.Index(fields=["institution", "learner", "exercise"])]


class ContentAccess(AutoReferenceModelMixin, InstitutionScopedModel):
    """Grants an institution access to a textbook under a licence."""

    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, related_name="access_grants")
    licence_reference = models.CharField(max_length=100, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institution", "textbook"], name="unique_textbook_access")
        ]
