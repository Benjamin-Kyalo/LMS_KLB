"""Course API endpoints."""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsStaff
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.courses.models import Assignment, Course, Lesson, LessonProgress, Module, Submission
from apps.courses.serializers import (
    AssignmentSerializer, CourseSerializer, LessonProgressSerializer,
    LessonSerializer, ModuleSerializer, SubmissionSerializer,
)


class CourseViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    filterset_fields = ["subject", "teacher", "status", "term", "academic_year"]
    search_fields = ["title", "code", "description"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class ModuleViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Module.objects.select_related("course")
    serializer_class = ModuleSerializer
    filterset_fields = ["course"]


class LessonViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related("module", "learning_outcome")
    serializer_class = LessonSerializer
    filterset_fields = ["module", "content_type", "is_downloadable"]
    search_fields = ["title", "content"]


class LessonProgressViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = LessonProgressSerializer
    filterset_fields = ["learner", "lesson", "status"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

    @action(detail=False, methods=["post"], url_path="mark-complete")
    def mark_complete(self, request):
        """Idempotent: safe to call again after an offline sync retry."""
        lesson_id = request.data.get("lesson")
        learner_id = request.data.get("learner")
        progress, created = LessonProgress.objects.update_or_create(
            lesson_id=lesson_id,
            learner_id=learner_id,
            institution=request.user.institution,
            defaults={
                "status": "COMPLETED",
                "completed_at": timezone.now(),
                "synced_at": timezone.now() if request.data.get("from_offline") else None,
            },
        )
        return Response(LessonProgressSerializer(progress).data)


class AssignmentViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related("course")
    serializer_class = AssignmentSerializer
    filterset_fields = ["course", "is_published"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, created_by=self.request.user)


class SubmissionViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Submission.objects.select_related("learner__user", "assignment")
    serializer_class = SubmissionSerializer
    filterset_fields = ["assignment", "learner", "status"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

    def get_permissions(self):
        # Learners may submit their own work; only staff may record grades.
        if self.action == "grade":
            return [IsAuthenticated(), IsStaff()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="grade")
    def grade(self, request, pk=None):
        submission = self.get_object()
        submission.score = request.data.get("score")
        submission.feedback = request.data.get("feedback", "")
        submission.status = "GRADED"
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        return Response(SubmissionSerializer(submission).data)
