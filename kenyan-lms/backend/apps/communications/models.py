"""Announcements, messages and notifications."""
from django.db import models

from apps.core.models import InstitutionScopedModel


class Announcement(InstitutionScopedModel):
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience_roles = models.JSONField(
        default=list, help_text="List of role codes; empty means everyone in the institution"
    )
    published_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-published_at", "-created_at"]


class Notification(models.Model):
    recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    notification_type = models.CharField(
        max_length=30, default="GENERAL",
        choices=[("GENERAL", "General"), ("ACADEMIC", "Academic"), ("ATTENDANCE", "Attendance"), ("MESSAGE", "Message"), ("SYSTEM", "System")],
    )
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]


class Message(models.Model):
    """Direct teacher-parent communication, always scoped via participants."""

    sender = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="received_messages")
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]


class NotificationPreference(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="notification_preferences")
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)
    types = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username} preferences"
