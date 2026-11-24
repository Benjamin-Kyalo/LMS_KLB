"""Communication serializers."""
from rest_framework import serializers

from apps.communications.models import Announcement, Message, Notification, NotificationPreference


class AnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="published_by.full_name", read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["institution", "published_by", "published_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["recipient", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    recipient_name = serializers.CharField(source="recipient.full_name", read_only=True)

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender", "sent_at", "is_read"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ["user"]
