"""Communication API endpoints."""
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.communications.models import Announcement, Message, Notification, NotificationPreference
from apps.communications.serializers import (
    AnnouncementSerializer, MessageSerializer, NotificationPreferenceSerializer, NotificationSerializer,
)
from apps.core.constants import Capabilities, Roles
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin


class AnnouncementViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.COMMUNICATIONS_MANAGE
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("published_by")
        user = self.request.user
        if self.action == "list":
            qs = qs.filter(is_published=True)
            if not user.is_platform_user:
                # Show announcements aimed at everyone or this user's role.
                from django.db.models import Q
                qs = qs.filter(Q(audience_roles=[]) | Q(audience_roles__contains=user.role))
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            announcement = serializer.save(
                institution=self.request.user.institution,
                published_by=self.request.user,
            )
            if announcement.is_published:
                announcement.published_at = timezone.now()
                announcement.save(update_fields=["published_at"])

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        announcement = self.get_object()
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save()
        return Response({"detail": "Announcement published."})


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user) | Message.objects.filter(recipient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({"detail": "Marked as read."})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    ordering = ["id"]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
