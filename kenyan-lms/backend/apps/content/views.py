"""Digital publishing API endpoints."""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.content.models import (
    Chapter, ContentAccess, ContentResource, DigitalTextbook, Exercise,
    ExerciseAttempt, Publisher,
)
from apps.content.serializers import (
    ChapterDetailSerializer, ChapterSerializer, ContentAccessSerializer,
    ContentResourceSerializer, DigitalTextbookSerializer, ExerciseAttemptSerializer,
    ExerciseSerializer, PublisherSerializer, TextbookDetailSerializer,
)
from apps.core.permissions import IsContentCurator
from apps.core.viewsets import AdminWriteMixin, ContentWriteMixin, InstitutionScopedQuerysetMixin


class PublishActionMixin:
    """Small reusable action for models with a status field."""

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        obj = self.get_object()
        obj.status = "PUBLISHED"
        obj.published_at = timezone.now()
        obj.save()
        return Response({"detail": "Published.", "id": obj.pk})


class PublisherInfoViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    search_fields = ["name"]


class DigitalTextbookViewSet(PublishActionMixin, viewsets.ModelViewSet):
    queryset = DigitalTextbook.objects.select_related("publisher", "subject", "education_level")
    serializer_class = DigitalTextbookSerializer
    filterset_fields = ["status", "subject", "education_level", "publisher"]
    search_fields = ["title", "isbn", "description"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TextbookDetailSerializer
        return DigitalTextbookSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "publish"}:
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated(), IsContentCurator()]
        return super().get_permissions()


class ChapterViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Chapter.objects.select_related("textbook")
    serializer_class = ChapterSerializer
    filterset_fields = ["textbook"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChapterDetailSerializer
        return ChapterSerializer


class ContentResourceViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = ContentResource.objects.select_related("chapter", "textbook")
    serializer_class = ContentResourceSerializer
    filterset_fields = ["chapter", "textbook", "resource_type", "offline_available"]


class ExerciseViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Exercise.objects.select_related("chapter")
    serializer_class = ExerciseSerializer
    filterset_fields = ["chapter"]


class ExerciseAttemptViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ExerciseAttemptSerializer
    filterset_fields = ["exercise", "learner"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class ContentAccessViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ContentAccessSerializer
    filterset_fields = ["textbook", "is_active"]


class AvailableTextbookViewSet(viewsets.ReadOnlyModelViewSet):
    """Textbooks the logged-in institution is licensed to use."""

    serializer_class = DigitalTextbookSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_platform_user:
            return DigitalTextbook.objects.filter(status="PUBLISHED")
        if not user.institution_id:
            return DigitalTextbook.objects.none()
        return DigitalTextbook.objects.filter(
            status="PUBLISHED",
            access_grants__institution_id=user.institution_id,
            access_grants__is_active=True,
        ).distinct()
