"""Course API endpoints."""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import Capabilities
from apps.core.permissions import staff_or_capability_permission
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.courses.models import Assignment, Course, Lesson, LessonProgress, Module, Submission
from apps.courses.serializers import (
    AssignmentSerializer, CourseSerializer, GradeSubmissionSerializer,
    LessonProgressSerializer, LessonSerializer, MarkLessonCompleteSerializer,
    ModuleSerializer, SubmissionSerializer, is_staff_user,
)


def _require_staff_learner(serializer):
    if serializer.validated_data.get("learner") is None:
        raise ValidationError({"learner": "This field is required for staff."})


class CourseViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.COURSES_MANAGE
    serializer_class = CourseSerializer
    filterset_fields = ["subject", "teacher", "status", "term", "academic_year"]
    search_fields = ["title", "code", "description"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class ModuleViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.COURSES_MANAGE
    queryset = Module.objects.select_related("course")
    serializer_class = ModuleSerializer
    filterset_fields = ["course"]


class LessonViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.COURSES_MANAGE
    queryset = Lesson.objects.select_related("module", "learning_outcome")
    serializer_class = LessonSerializer
    filterset_fields = ["module", "content_type", "is_downloadable"]
    search_fields = ["title", "content"]


class LessonProgressViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = LessonProgressSerializer
    filterset_fields = ["learner", "lesson", "status"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not is_staff_user(user):
            return queryset.filter(learner__user=user)
        return queryset

    def _own_learner(self, user):
        learner = getattr(user, "learner_profile", None)
        if learner is None:
            raise ValidationError("Your account is not linked to a learner profile.")
        return learner

    def perform_create(self, serializer):
        if is_staff_user(self.request.user):
            _require_staff_learner(serializer)
            super().perform_create(serializer)
        else:
            learner = self._own_learner(self.request.user)
            serializer.save(institution=learner.institution, learner=learner)

    def perform_update(self, serializer):
        if is_staff_user(self.request.user):
            super().perform_update(serializer)
        else:
            learner = self._own_learner(self.request.user)
            serializer.save(institution=learner.institution, learner=learner)

    @action(detail=False, methods=["post"], url_path="mark-complete")
    def mark_complete(self, request):
        """Idempotent: safe to call again if the web request is retried."""
        serializer = MarkLessonCompleteSerializer(
            data=request.data, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        lesson = serializer.validated_data["lesson"]
        requested_learner = serializer.validated_data.get("learner")
        if is_staff_user(request.user):
            if requested_learner is None:
                raise ValidationError({"learner": "This field is required for staff."})
            learner = requested_learner
        else:
            learner = self._own_learner(request.user)
            if requested_learner is not None and requested_learner.pk != learner.pk:
                raise ValidationError({"learner": "You may only complete your own lessons."})
        progress, created = LessonProgress.objects.update_or_create(
            lesson=lesson,
            learner=learner,
            institution=request.user.institution or lesson.institution,
            defaults={
                "status": "COMPLETED",
                "completed_at": timezone.now(),
            },
        )
        return Response(LessonProgressSerializer(progress).data)


class AssignmentViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.COURSES_MANAGE
    queryset = Assignment.objects.select_related("course")
    serializer_class = AssignmentSerializer
    filterset_fields = ["course", "is_published"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, created_by=self.request.user)


class SubmissionViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Submission.objects.select_related("learner__user", "assignment")
    serializer_class = SubmissionSerializer
    filterset_fields = ["assignment", "learner", "status"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not is_staff_user(user):
            return queryset.filter(learner__user=user)
        return queryset

    def _own_learner(self, user):
        learner = getattr(user, "learner_profile", None)
        if learner is None:
            raise ValidationError("Your account is not linked to a learner profile.")
        return learner

    def perform_create(self, serializer):
        if is_staff_user(self.request.user):
            _require_staff_learner(serializer)
            super().perform_create(serializer)
        else:
            learner = self._own_learner(self.request.user)
            serializer.save(institution=learner.institution, learner=learner)

    def perform_update(self, serializer):
        if is_staff_user(self.request.user):
            super().perform_update(serializer)
        else:
            learner = self._own_learner(self.request.user)
            # Non-staff writes are confined to answer content and safe status.
            serializer.save(
                institution=learner.institution,
                learner=learner,
                assignment=serializer.instance.assignment,
            )

    def get_permissions(self):
        # Learners may submit their own work; only staff may record grades.
        if self.action == "grade":
            return [
                IsAuthenticated(),
                staff_or_capability_permission(Capabilities.ASSESSMENTS_MANAGE)(),
            ]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="grade")
    def grade(self, request, pk=None):
        submission = self.get_object()
        serializer = GradeSubmissionSerializer(
            data=request.data, context={"submission": submission},
        )
        serializer.is_valid(raise_exception=True)
        submission.score = serializer.validated_data["score"]
        submission.feedback = serializer.validated_data.get("feedback", "")
        submission.status = "GRADED"
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        return Response(SubmissionSerializer(submission).data)
