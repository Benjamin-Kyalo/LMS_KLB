"""Courses, modules, lessons and learner progress."""
from django.db import models

from apps.core.constants import ContentStatus
from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class Course(AutoReferenceModelMixin, InstitutionScopedModel):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    academic_year = models.ForeignKey("institutions.AcademicYear", on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey("institutions.Term", on_delete=models.SET_NULL, null=True, blank=True)
    education_level = models.ForeignKey("curriculum.EducationLevel", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ContentStatus.CHOICES, default=ContentStatus.DRAFT, db_index=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["institution", "status", "term"])]

    def __str__(self):
        return self.title


class Module(InstitutionScopedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["course", "sequence"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(InstitutionScopedModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    content_type = models.CharField(
        max_length=20, default="TEXT",
        choices=[("TEXT", "Text"), ("VIDEO", "Video"), ("AUDIO", "Audio"), ("INTERACTIVE", "Interactive")],
    )
    media_url = models.URLField(blank=True)
    learning_outcome = models.ForeignKey("curriculum.LearningOutcome", on_delete=models.SET_NULL, null=True, blank=True)
    estimated_minutes = models.PositiveSmallIntegerField(default=15)
    sequence = models.PositiveSmallIntegerField(default=1)
    is_downloadable = models.BooleanField(default=False, help_text="May be downloaded for later reading")

    class Meta:
        ordering = ["module", "sequence"]

    def __str__(self):
        return self.title


class LessonProgress(InstitutionScopedModel):
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    status = models.CharField(
        max_length=20, default="NOT_STARTED",
        choices=[("NOT_STARTED", "Not started"), ("IN_PROGRESS", "In progress"), ("COMPLETED", "Completed")],
    )
    time_spent_seconds = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True, help_text="Legacy timestamp retained for existing records")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["learner", "lesson"], name="unique_learner_lesson_progress")
        ]
        indexes = [models.Index(fields=["institution", "learner", "status"])]


class Assignment(InstitutionScopedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    rubric = models.ForeignKey(
        "curriculum.Rubric", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assignments",
    )
    allow_resubmission = models.BooleanField(default=False)
    max_attempts = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]


class Submission(InstitutionScopedModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="submissions")
    text_answer = models.TextField(blank=True)
    attachment = models.FileField(upload_to="submissions/", null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, default="SUBMITTED",
        choices=[("DRAFT", "Draft"), ("SUBMITTED", "Submitted"), ("GRADED", "Graded"), ("RETURNED", "Returned")],
    )
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="graded_submissions")
    graded_at = models.DateTimeField(null=True, blank=True)
    rubric_level = models.ForeignKey(
        "curriculum.RubricLevel", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="submissions",
    )
    rubric_level_name = models.CharField(max_length=100, blank=True)
    rubric_max_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    private_notes = models.TextField(blank=True)
    feedback_published_at = models.DateTimeField(null=True, blank=True)
    current_attempt = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(fields=["assignment", "learner"], name="unique_submission_per_assignment")
        ]


class SubmissionAttempt(InstitutionScopedModel):
    """An immutable snapshot of one submission attempt and its returned grade."""

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField()
    text_answer = models.TextField(blank=True)
    attachment = models.FileField(upload_to="submission-attempts/", null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["submission", "attempt_number"]
        constraints = [
            models.UniqueConstraint(fields=["submission", "attempt_number"], name="unique_submission_attempt_number")
        ]

    def __str__(self):
        return f"{self.submission_id} - attempt {self.attempt_number}"


class SubmissionCriterionScore(InstitutionScopedModel):
    """A criterion-level mark with a snapshot of the criterion definition."""

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="criterion_scores")
    criterion = models.ForeignKey(
        "curriculum.RubricCriterion", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="scores",
    )
    attempt_number = models.PositiveSmallIntegerField(default=1)
    criterion_name = models.CharField(max_length=150)
    max_score = models.DecimalField(max_digits=6, decimal_places=2)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "attempt_number", "criterion"],
                name="unique_criterion_score_per_attempt",
            )
        ]

    def __str__(self):
        return f"{self.criterion_name}: {self.score}/{self.max_score}"
