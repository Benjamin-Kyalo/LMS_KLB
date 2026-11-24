"""Version-aware Kenyan curriculum structures (CBE/CBC)."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel, TimeStampedModel


class CurriculumFramework(AutoReferenceModelMixin, TimeStampedModel):
    """A named, versioned framework, e.g. 'KICD CBC 2017' or a TVET syllabus."""

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    version = models.CharField(max_length=20, default="1.0")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "version"]
        constraints = [
            models.UniqueConstraint(fields=["name", "version"], name="unique_framework_version")
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class EducationLevel(AutoReferenceModelMixin, TimeStampedModel):
    framework = models.ForeignKey(CurriculumFramework, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["framework", "sequence", "name"]
        constraints = [
            models.UniqueConstraint(fields=["framework", "code"], name="unique_level_code_per_framework")
        ]

    def __str__(self):
        return self.name


class LearningArea(AutoReferenceModelMixin, TimeStampedModel):
    level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name="learning_areas")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["level", "sequence", "name"]

    def __str__(self):
        return self.name


class Strand(AutoReferenceModelMixin, TimeStampedModel):
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name="strands")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["learning_area", "sequence", "name"]

    def __str__(self):
        return self.name


class SubStrand(AutoReferenceModelMixin, TimeStampedModel):
    strand = models.ForeignKey(Strand, on_delete=models.CASCADE, related_name="sub_strands")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)
    recommended_hours = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["strand", "sequence", "name"]

    def __str__(self):
        return self.name


class LearningOutcome(AutoReferenceModelMixin, TimeStampedModel):
    """A specific, assessable outcome. Never hardcode these - import them."""

    sub_strand = models.ForeignKey(SubStrand, on_delete=models.CASCADE, related_name="outcomes")
    code = models.CharField(max_length=50)
    description = models.TextField()
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["sub_strand", "sequence"]
        constraints = [
            models.UniqueConstraint(fields=["sub_strand", "code"], name="unique_outcome_code_per_strand")
        ]

    def __str__(self):
        return f"{self.code}: {self.description[:60]}"


class Competency(AutoReferenceModelMixin, TimeStampedModel):
    framework = models.ForeignKey(CurriculumFramework, on_delete=models.CASCADE, related_name="competencies")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["framework", "name"]

    def __str__(self):
        return self.name


class Rubric(TimeStampedModel):
    """A configurable achievement rubric, shared or institution-specific."""

    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.CASCADE, null=True, blank=True, related_name="rubrics"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RubricLevel(TimeStampedModel):
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=100)
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    description = models.TextField(blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["rubric", "sequence"]

    def __str__(self):
        return f"{self.rubric.name} - {self.name}"


class CompetencyEvidence(InstitutionScopedModel):
    """Records observed evidence of a learner's progress toward an outcome."""

    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="competency_evidence")
    outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
    rubric_level = models.ForeignKey(RubricLevel, on_delete=models.SET_NULL, null=True, blank=True)
    achieved_level = models.CharField(
        max_length=20,
        choices=[("BEGINNING", "Beginning"), ("DEVELOPING", "Developing"), ("ACHIEVING", "Achieving"), ("EXTENDING", "Extending")],
        blank=True,
    )
    evidence_type = models.CharField(
        max_length=30, default="OBSERVATION",
        choices=[("OBSERVATION", "Observation"), ("ASSIGNMENT", "Assignment"), ("QUIZ", "Quiz"), ("PORTFOLIO", "Portfolio")],
    )
    notes = models.TextField(blank=True)
    evidence_url = models.URLField(blank=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["institution", "learner", "achieved_level"])]
