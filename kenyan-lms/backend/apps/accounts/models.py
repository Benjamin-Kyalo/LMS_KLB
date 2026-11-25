"""Custom user model and secure administrator invitations."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.core.constants import Capabilities, Roles
from apps.core.models import TimeStampedModel


class CustomRole(TimeStampedModel):
    """A named, reusable set of capabilities created by an administrator."""

    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custom_roles",
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_custom_roles",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="accounts_customrole_unique_institution_name",
            )
        ]

    def __str__(self):
        return self.name

    @property
    def capabilities(self):
        values = self.permissions or []
        if isinstance(values, dict):
            values = [key for key, enabled in values.items() if enabled]
        return sorted(value for value in values if value in Capabilities.ALL)


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
    custom_role = models.ForeignKey(
        CustomRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    must_change_password = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [models.Index(fields=["role", "institution"])]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_super_admin(self):
        return self.role == Roles.SUPER_ADMIN

    @property
    def is_platform_user(self):
        return self.is_super_admin

    @property
    def is_institution_admin(self):
        return self.role in Roles.ADMIN_ROLES

    @property
    def capabilities(self):
        if self.role in Roles.ADMIN_ROLES:
            return sorted(Capabilities.ALL)
        if self.role == Roles.CUSTOM and self.custom_role_id and self.custom_role.is_active:
            return self.custom_role.capabilities
        return []

    def has_capability(self, capability):
        if self.role in Roles.ADMIN_ROLES:
            return True
        return capability in self.capabilities


class OnboardingProfile(TimeStampedModel):
    """Tracks first-run completion for each authenticated role.

    Approval and linking flags are written by the approval/link workflows, not
    by the account owner. ``profile_complete`` is the only flag the owner can
    confirm from the onboarding screen.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="onboarding_profile"
    )
    profile_complete = models.BooleanField(default=False)
    teacher_approved = models.BooleanField(default=False)
    classes_assigned = models.BooleanField(default=False)
    guardian_link_verified = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Onboarding: {self.user.username}"

    @property
    def is_complete(self):
        role = self.user.role
        if role == Roles.TEACHER:
            return self.profile_complete and self.teacher_approved and self.classes_assigned
        if role == Roles.GUARDIAN:
            return self.profile_complete and self.guardian_link_verified
        return self.profile_complete

    def steps(self):
        """Return plain-language checklist items for the frontend."""
        role = self.user.role
        items = [{
            "key": "profile_complete",
            "label": "Confirm your profile details",
            "done": self.profile_complete,
        }]
        if role == Roles.TEACHER:
            items.extend([
                {
                    "key": "teacher_approved",
                    "label": "School administrator approves your account",
                    "done": self.teacher_approved,
                },
                {
                    "key": "classes_assigned",
                    "label": "You are assigned to at least one class",
                    "done": self.classes_assigned,
                },
            ])
        elif role == Roles.GUARDIAN:
            items.append({
                "key": "guardian_link_verified",
                "label": "Your learner link is verified",
                "done": self.guardian_link_verified,
            })
        return items

    def mark_complete_if_ready(self):
        if self.is_complete and not self.completed_at:
            self.completed_at = timezone.now()
            self.save(update_fields=["completed_at", "updated_at"])
        return self.completed_at


@receiver(post_save, sender=User)
def ensure_onboarding_profile(sender, instance, created, **kwargs):
    """Every account gets an onboarding record, regardless of creation path."""
    if created:
        OnboardingProfile.objects.get_or_create(user=instance)


class AdminInvitation(models.Model):
    """A single-use, expiring invitation for an administrator account."""

    ADMIN_ROLE_CHOICES = [
        (Roles.ADMIN, "Administrator"),
        (Roles.CUSTOM, "Custom Role"),
    ]

    email = models.EmailField()
    role = models.CharField(max_length=30, choices=ADMIN_ROLE_CHOICES)
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="admin_invitations",
    )
    custom_role = models.ForeignKey(
        CustomRole, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invitations",
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


class LoginAttempt(models.Model):
    """Counter for failed sign-in attempts from one IP and username pair."""

    ip_address = models.CharField(max_length=64, default="unknown")
    username = models.CharField(max_length=150)
    failed_count = models.PositiveIntegerField(default=0)
    first_failed_at = models.DateTimeField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_failed_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["ip_address", "username"],
                name="accounts_login_attempt_ip_username_unique",
            )
        ]

    def __str__(self):
        return f"{self.username} from {self.ip_address}: {self.failed_count}"


class PasswordResetUse(models.Model):
    """A spent reset token. Tokens are never accepted twice."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="used_password_resets"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-used_at"]

    def __str__(self):
        return f"Used reset token for {self.user.username}"
