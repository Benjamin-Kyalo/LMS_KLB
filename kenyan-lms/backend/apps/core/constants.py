"""Shared choices. Keep all role, capability and status labels in one place."""


class Roles:
    """Simplified built-in roles.

    ``CUSTOM`` is a role kind: the display name comes from
    ``accounts.CustomRole`` and the account carries a ``custom_role`` id.
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    CUSTOM = "CUSTOM"
    TEACHER = "TEACHER"
    LEARNER = "LEARNER"
    GUARDIAN = "GUARDIAN"

    CHOICES = [
        (SUPER_ADMIN, "Super Administrator"),
        (ADMIN, "Administrator"),
        (CUSTOM, "Custom Role"),
        (TEACHER, "Teacher"),
        (LEARNER, "Learner"),
        (GUARDIAN, "Parent or Guardian"),
    ]

    # Super admin is the only global role. Admin holds every authority inside
    # its own institution. Custom roles are limited to their picked capabilities.
    PLATFORM_ROLES = {SUPER_ADMIN}
    INSTITUTION_ADMIN_ROLES = {ADMIN}
    ADMIN_ROLES = PLATFORM_ROLES | INSTITUTION_ADMIN_ROLES
    STAFF_ROLES = ADMIN_ROLES | {TEACHER, CUSTOM}
    PUBLIC_REGISTRATION_ROLES = {LEARNER, GUARDIAN, TEACHER}
    ASSIGNABLE_BUILTINS = {ADMIN, TEACHER, LEARNER, GUARDIAN}


class Capabilities:
    """Allowlisted permissions that a custom role may carry."""

    ADMIN_ACCESS = "admin.access"
    USERS_MANAGE = "users.manage"
    ROLES_MANAGE = "roles.manage"
    ACADEMICS_MANAGE = "academics.manage"
    LEARNERS_MANAGE = "learners.manage"
    TEACHERS_MANAGE = "teachers.manage"
    GUARDIANS_MANAGE = "guardians.manage"
    COURSES_MANAGE = "courses.manage"
    ASSESSMENTS_MANAGE = "assessments.manage"
    CONTENT_MANAGE = "content.manage"
    ATTENDANCE_MANAGE = "attendance.manage"
    FEES_MANAGE = "fees.manage"
    COMMUNICATIONS_MANAGE = "communications.manage"
    REPORTS_VIEW = "reports.view"
    APPEARANCE_MANAGE = "appearance.manage"
    INSTITUTIONS_MANAGE = "institutions.manage"
    TUTOR_USE = "tutor.use"

    ALL = {
        ADMIN_ACCESS, USERS_MANAGE, ROLES_MANAGE, ACADEMICS_MANAGE,
        LEARNERS_MANAGE, TEACHERS_MANAGE, GUARDIANS_MANAGE,
        COURSES_MANAGE, ASSESSMENTS_MANAGE, CONTENT_MANAGE,
        ATTENDANCE_MANAGE, FEES_MANAGE, COMMUNICATIONS_MANAGE,
        REPORTS_VIEW, APPEARANCE_MANAGE, INSTITUTIONS_MANAGE, TUTOR_USE,
    }

    GROUPS = [
        ("Access", [ADMIN_ACCESS, TUTOR_USE]),
        ("People", [USERS_MANAGE, ROLES_MANAGE, LEARNERS_MANAGE,
                    TEACHERS_MANAGE, GUARDIANS_MANAGE]),
        ("Learning", [ACADEMICS_MANAGE, COURSES_MANAGE, ASSESSMENTS_MANAGE,
                      CONTENT_MANAGE, ATTENDANCE_MANAGE]),
        ("Operations", [FEES_MANAGE, COMMUNICATIONS_MANAGE, REPORTS_VIEW,
                        APPEARANCE_MANAGE, INSTITUTIONS_MANAGE]),
    ]

    LABELS = {
        ADMIN_ACCESS: "Enter the administration portal",
        USERS_MANAGE: "Manage users and account status",
        ROLES_MANAGE: "Create and edit custom roles",
        ACADEMICS_MANAGE: "Manage terms, classes, subjects and timetables",
        LEARNERS_MANAGE: "Manage learner records",
        TEACHERS_MANAGE: "Manage teacher records and approvals",
        GUARDIANS_MANAGE: "Manage guardians and learner links",
        COURSES_MANAGE: "Manage courses and lessons",
        ASSESSMENTS_MANAGE: "Manage quizzes, exams and grading",
        CONTENT_MANAGE: "Manage the digital library and publishing",
        ATTENDANCE_MANAGE: "Manage attendance",
        FEES_MANAGE: "Manage invoices, structures and payments",
        COMMUNICATIONS_MANAGE: "Manage announcements and messages",
        REPORTS_VIEW: "View reports and analytics",
        APPEARANCE_MANAGE: "Manage public appearance and wording",
        INSTITUTIONS_MANAGE: "Manage institution records",
        TUTOR_USE: "Use the AI tutor",
    }


class ResourceAccessScope:
    """Who may discover and open a published resource."""

    PUBLIC = "PUBLIC"
    INSTITUTION = "INSTITUTION"
    CLASS = "CLASS"
    CHOICES = [
        (PUBLIC, "Public"),
        (INSTITUTION, "My institution"),
        (CLASS, "Selected class"),
    ]


class ResourceDelivery:
    """How a learning resource is delivered to the reader."""

    UPLOAD = "UPLOAD"
    LINK = "LINK"
    EMBED = "EMBED"
    CHOICES = [
        (UPLOAD, "Local upload"),
        (LINK, "External link"),
        (EMBED, "Curated embed"),
    ]


class EmbedProviderKind:
    YOUTUBE = "YOUTUBE"
    VIMEO = "VIMEO"
    CHOICES = [
        (YOUTUBE, "YouTube"),
        (VIMEO, "Vimeo"),
    ]


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
