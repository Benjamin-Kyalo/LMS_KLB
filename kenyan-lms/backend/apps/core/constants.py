"""Shared choices. Keep all role and status labels in one place."""


class Roles:
    SUPER_ADMIN = "SUPER_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"
    LEARNER = "LEARNER"
    GUARDIAN = "GUARDIAN"
    CONTENT_MANAGER = "CONTENT_MANAGER"

    CHOICES = [
        (SUPER_ADMIN, "Platform Super Administrator"),
        (PLATFORM_ADMIN, "Platform Administrator"),
        (INSTITUTION_ADMIN, "Institution Administrator"),
        (SCHOOL_ADMIN, "School Administrator"),
        (TEACHER, "Teacher"),
        (LEARNER, "Learner"),
        (GUARDIAN, "Parent or Guardian"),
        (CONTENT_MANAGER, "Content Manager"),
    ]

    PLATFORM_ROLES = {SUPER_ADMIN, PLATFORM_ADMIN}
    INSTITUTION_ADMIN_ROLES = {INSTITUTION_ADMIN, SCHOOL_ADMIN}
    # Platform administrators hold every authority, including staff actions,
    # so they must be included here. Without them, an orphan report snapshot
    # fails with 403 before its validation can explain the missing institution.
    STAFF_ROLES = PLATFORM_ROLES | {TEACHER, CONTENT_MANAGER} | INSTITUTION_ADMIN_ROLES


class AttendanceStatus:
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"
    CHOICES = [
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (LATE, "Late"),
        (EXCUSED, "Excused"),
    ]


class MasteryLevel:
    BEGINNING = "BEGINNING"
    DEVELOPING = "DEVELOPING"
    ACHIEVING = "ACHIEVING"
    EXTENDING = "EXTENDING"
    CHOICES = [
        (BEGINNING, "Beginning"),
        (DEVELOPING, "Developing"),
        (ACHIEVING, "Achieving"),
        (EXTENDING, "Extending"),
    ]


class ContentStatus:
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    CHOICES = [
        (DRAFT, "Draft"),
        (IN_REVIEW, "In review"),
        (APPROVED, "Approved"),
        (PUBLISHED, "Published"),
        (ARCHIVED, "Archived"),
    ]
