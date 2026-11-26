"""Communication serializers."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.communications.models import Announcement, Message, Notification, NotificationPreference


class AnnouncementSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    author_name = serializers.CharField(source="published_by.full_name", read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["institution", "published_by", "published_at"]


class NotificationSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        # Notifications are created only by server-side event handlers; the
        # API is read-only apart from explicit mark-read actions.
        read_only_fields = ["id", "recipient", "created_at", "title", "body", "notification_type", "link", "is_read"]


class MessageSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    recipient_name = serializers.CharField(source="recipient.full_name", read_only=True)

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender", "sent_at", "is_read"]


class NotificationPreferenceSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ["user"]
