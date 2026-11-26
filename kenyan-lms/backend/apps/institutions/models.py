"""Institution profile and academic structure."""
from django.db import models

from apps.core.models import AutoReferenceModelMixin, TimeStampedModel


class InstitutionType(AutoReferenceModelMixin, TimeStampedModel):
    """Primary, junior, senior, TVET, college, university, etc."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Institution(AutoReferenceModelMixin, TimeStampedModel):
    """One school or training institution. Owns all of its own data."""

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    institution_type = models.ForeignKey(
        InstitutionType, on_delete=models.PROTECT, related_name="institutions"
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    motto = models.CharField(max_length=200, blank=True)
    # School logo shown in both the admin panel and the learner/guardian portal.
    # Keep the image small so modest connections can load the portal quickly.
    logo = models.ImageField(upload_to="institutions/logos/", blank=True)
    address_line = models.CharField(max_length=200, blank=True)
    town = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True, db_index=True)
    sub_county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["county", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(AutoReferenceModelMixin, TimeStampedModel):
    """An organisational unit inside a school, e.g. Mathematics or Guidance."""

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    head_of_department = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"], name="unique_department_per_institution"
            )
        ]

    def __str__(self):
        return self.name


class AcademicYear(TimeStampedModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="academic_years")
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"], name="unique_academic_year_per_institution"
            )
        ]

    def __str__(self):
        return self.name


class Term(TimeStampedModel):
    """Configurable terms - private schools may not use three terms."""

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="terms")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=50)
    sequence = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["academic_year", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "name"], name="unique_term_per_year"
            )
        ]

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"


class SchoolClass(TimeStampedModel):
    """A class or year group, optionally split into streams."""

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="classes")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=80)
    level = models.CharField(max_length=50, blank=True, db_index=True)
    stream = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=40)
    # NOTE: the class teacher is recorded in teachers.TeacherClassAssignment
    # (is_class_teacher=True). Keeping that relationship in one place avoids a
    # circular dependency between the institutions and teachers apps.

    class Meta:
        ordering = ["level", "name", "stream"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "academic_year", "name", "stream"],
                name="unique_class_per_year",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.stream}".strip()

    @property
    def display_name(self):
        """Unique, readable label for dropdowns and table cells."""
        return self.__str__()


class Subject(AutoReferenceModelMixin, TimeStampedModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)
    learning_area = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["institution", "name"], name="unique_subject_per_institution")
        ]

    def __str__(self):
        return self.name
