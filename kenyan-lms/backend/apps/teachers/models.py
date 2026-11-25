"""Teacher profiles, class allocations and lesson plans."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class Teacher(AutoReferenceModelMixin, InstitutionScopedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="teacher_profile")
    staff_number = models.CharField(max_length=50, blank=True)
    employment_type = models.CharField(
        max_length=20, default="PERMANENT",
        choices=[("PERMANENT", "Permanent"), ("CONTRACT", "Contract"), ("PART_TIME", "Part time"), ("VOLUNTEER", "Volunteer")],
    )
    phone = models.CharField(max_length=20, blank=True)
    subjects = models.ManyToManyField("institutions.Subject", blank=True, related_name="teachers")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        return f"{self.user.full_name} ({self.staff_number})"


class TeacherApproval(AutoReferenceModelMixin, InstitutionScopedModel):
    """Account approval workflow for teachers who registered publicly."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="approval_records")
    reference = models.CharField(max_length=50, blank=True, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="teacher_approval_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.teacher.user.full_name} — {self.get_status_display()}"


class TeacherClassAssignment(InstitutionScopedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="assignments")
    school_class = models.ForeignKey("institutions.SchoolClass", on_delete=models.CASCADE, related_name="teacher_assignments")
    subject = models.ForeignKey("institutions.Subject", on_delete=models.CASCADE, related_name="teacher_assignments")
    academic_year = models.ForeignKey("institutions.AcademicYear", on_delete=models.CASCADE)
    term = models.ForeignKey("institutions.Term", on_delete=models.SET_NULL, null=True, blank=True)
    is_class_teacher = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "school_class", "subject", "academic_year"],
                name="unique_teacher_assignment",
            )
        ]


class LessonPlan(InstitutionScopedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="lesson_plans")
    school_class = models.ForeignKey("institutions.SchoolClass", on_delete=models.CASCADE, related_name="lesson_plans")
    subject = models.ForeignKey("institutions.Subject", on_delete=models.CASCADE, related_name="lesson_plans")
    title = models.CharField(max_length=200)
    objectives = models.TextField()
    content = models.TextField(blank=True)
    planned_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, default="DRAFT",
        choices=[("DRAFT", "Draft"), ("SUBMITTED", "Submitted"), ("APPROVED", "Approved")],
    )

    def __str__(self):
        return self.title
