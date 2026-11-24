"""Question banks, quizzes, exams and results."""
from django.db import models

from apps.core.models import InstitutionScopedModel


class Question(InstitutionScopedModel):
    QUESTION_TYPES = [
        ("MCQ", "Multiple choice"),
        ("TRUE_FALSE", "True or false"),
        ("SHORT", "Short answer"),
        ("ESSAY", "Essay"),
    ]

    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    learning_outcome = models.ForeignKey("curriculum.LearningOutcome", on_delete=models.SET_NULL, null=True, blank=True)
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default="MCQ")
    text = models.TextField()
    options = models.JSONField(default=list, blank=True, help_text="List of option strings for MCQ")
    correct_answer = models.CharField(max_length=500, blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    explanation = models.TextField(blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:80]


class Quiz(InstitutionScopedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes")
    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    time_limit_minutes = models.PositiveSmallIntegerField(default=30)
    is_published = models.BooleanField(default=False)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    sequence = models.PositiveSmallIntegerField(default=1)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    class Meta:
        ordering = ["quiz", "sequence"]
        constraints = [models.UniqueConstraint(fields=["quiz", "question"], name="unique_question_per_quiz")]


class QuizAttempt(InstitutionScopedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="quiz_attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, default="IN_PROGRESS",
        choices=[("IN_PROGRESS", "In progress"), ("COMPLETED", "Completed"), ("SYNCED", "Synced from offline")],
    )
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["institution", "quiz", "learner"])]


class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["attempt", "question"], name="unique_answer_per_attempt")]


class Exam(InstitutionScopedModel):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    school_class = models.ForeignKey("institutions.SchoolClass", on_delete=models.SET_NULL, null=True, blank=True)
    term = models.ForeignKey("institutions.Term", on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.ForeignKey("institutions.AcademicYear", on_delete=models.SET_NULL, null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)

    class Meta:
        ordering = ["-exam_date", "title"]


class ExamResult(InstitutionScopedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="exam_results")
    score = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.CharField(max_length=10, blank=True)
    position = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["exam", "learner"], name="unique_result_per_exam")]
        indexes = [models.Index(fields=["institution", "exam", "learner"])]
