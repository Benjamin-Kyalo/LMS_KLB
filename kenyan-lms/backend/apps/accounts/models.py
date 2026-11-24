"""Custom user model and secure administrator invitations."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from apps.core.constants import Roles


class LmsUserManager(UserManager):
    """Keep Django's superuser flow aligned with the project's role checks."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Roles.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """One login account per person. Role decides what they may do."""

    objects = LmsUserManager()

    role = models.CharField(max_length=30, choices=Roles.CHOICES, default=Roles.LEARNER, db_index=True)
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    phone = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=10, default="en")
    must_change_password = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [models.Index(fields=["role", "institution"])]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_platform_user(self):
        return self.role in Roles.PLATFORM_ROLES

    @property
    def is_institution_admin(self):
        return self.role in Roles.INSTITUTION_ADMIN_ROLES


class AdminInvitation(models.Model):
    """A single-use, expiring invitation for an administrator account."""

    ADMIN_ROLE_CHOICES = [
        (Roles.PLATFORM_ADMIN, "Platform Administrator"),
        (Roles.INSTITUTION_ADMIN, "Institution Administrator"),
        (Roles.SCHOOL_ADMIN, "School Administrator"),
    ]

    email = models.EmailField()
    role = models.CharField(max_length=30, choices=ADMIN_ROLE_CHOICES)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="admin_invitations",
    )
    token = models.CharField(max_length=128, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sent_admin_invitations",
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_usable(self):
        return not self.revoked and self.accepted_at is None and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.email} ({self.role})"
