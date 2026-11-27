"""Course API endpoints."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.communications.services import notify_user
from apps.core.audit import log_audit, record_change, snapshot
from apps.core.constants import Capabilities
from apps.core.permissions import staff_or_capability_permission
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.courses.models import (
    Assignment, Course, Lesson, LessonProgress, Module, Submission,
    SubmissionAttempt, SubmissionCriterionScore,
)
from apps.courses.serializers import (
    AssignmentSerializer, CourseSerializer, GradeSubmissionSerializer,
    GradeWithRubricSerializer, LessonProgressSerializer, LessonSerializer,
    MarkLessonCompleteSerializer, ModuleSerializer, ResubmitSerializer,
    SubmissionSerializer, is_staff_user,
)
from apps.learners.models import LearnerGuardian


def _require_staff_learner(serializer):
    if serializer.validated_data.get("learner") is None:
        raise ValidationError({"learner": "This field is required for staff."})


def _rubric_level_for(rubric, total, max_score):
    """Resolve the achievement band from the final percentage, never from the client."""
    if rubric is None or not max_score:
        return None
    percentage = (total / max_score) * Decimal("100")
    return rubric.levels.filter(
        min_score__lte=percentage, max_score__gte=percentage
    ).order_by("sequence", "min_score").first()


def _graded_staff_actions():
    return [
        IsAuthenticated(),
        staff_or_capability_permission(Capabilities.ASSESSMENTS_MANAGE)(),
    ]


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
        if not user.is_authenticated or is_staff_user(user):
            return queryset
        if user.role == "GUARDIAN":
            learner_ids = LearnerGuardian.objects.filter(
                guardian__user=user, is_verified=True, can_view_academics=True
            ).values_list("learner_id", flat=True)
            return queryset.filter(learner_id__in=learner_ids)
        return queryset.filter(learner__user=user)

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
        # Learners may submit their own work; only staff may record or publish grades.
        if self.action in {"grade", "grade_with_rubric", "publish_feedback"}:
            return _graded_staff_actions()
        return super().get_permissions()

    def _detail(self, submission, request):
        return Response(
            SubmissionSerializer(submission, context={"request": request}).data
        )

    @action(detail=True, methods=["post"], url_path="grade")
    def grade(self, request, pk=None):
        submission = self.get_object()
        serializer = GradeSubmissionSerializer(
            data=request.data, context={"submission": submission, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            before = snapshot(submission)
            submission.score = serializer.validated_data["score"]
            submission.feedback = serializer.validated_data.get("feedback", "")
            submission.status = "GRADED"
            submission.graded_by = request.user
            submission.graded_at = timezone.now()
            submission.rubric_level = None
            submission.rubric_level_name = ""
            submission.rubric_max_score = None
            submission.save()
            SubmissionCriterionScore.objects.filter(
                submission=submission, attempt_number=submission.current_attempt
            ).delete()
            record_change(
                request.user, submission, before, snapshot(submission),
                action="submission.graded", request=request,
            )
        return self._detail(submission, request)

    @action(detail=True, methods=["post"], url_path="grade-rubric", url_name="grade-rubric")
    def grade_with_rubric(self, request, pk=None):
        submission = self.get_object()
        serializer = GradeWithRubricSerializer(
            data=request.data, context={"submission": submission, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        rubric = submission.assignment.rubric
        criteria = serializer.validated_data["criteria"]
        with transaction.atomic():
            before = snapshot(submission)
            SubmissionCriterionScore.objects.filter(
                submission=submission, attempt_number=submission.current_attempt
            ).delete()
            for row in criteria:
                criterion = row["criterion"]
                SubmissionCriterionScore.objects.create(
                    institution=submission.institution,
                    submission=submission,
                    criterion=criterion,
                    attempt_number=submission.current_attempt,
                    criterion_name=criterion.name,
                    max_score=criterion.max_score,
                    score=row["score"],
                    comment=row.get("comment", ""),
                )

            total = serializer.validated_data["total_score"]
            level = _rubric_level_for(rubric, total, submission.assignment.max_score)
            submission.score = total
            submission.feedback = serializer.validated_data.get("overall_feedback", "")
            submission.private_notes = serializer.validated_data.get("private_notes", "")
            submission.status = "GRADED"
            submission.graded_by = request.user
            submission.graded_at = timezone.now()
            submission.rubric_level = level
            submission.rubric_level_name = level.name if level else ""
            submission.rubric_max_score = submission.assignment.max_score
            submission.save()
            record_change(
                request.user, submission, before, snapshot(submission),
                action="submission.rubric_graded", request=request,
            )
            log_audit(
                request.user, "submission.rubric_scores", "Submission", submission.pk,
                {
                    "attempt": submission.current_attempt,
                    "criteria": [
                        {
                            "criterion_id": row["criterion"].pk,
                            "criterion": row["criterion"].name,
                            "score": str(row["score"]),
                            "max_score": str(row["criterion"].max_score),
                        }
                        for row in criteria
                    ],
                },
                institution=submission.institution_id,
                request=request,
            )
        return self._detail(submission, request)

    @action(detail=True, methods=["post"], url_path="publish-feedback", url_name="publish-feedback")
    def publish_feedback(self, request, pk=None):
        submission = self.get_object()
        if submission.graded_at is None:
            raise ValidationError("Grade the submission before publishing feedback.")
        if submission.feedback_published_at:
            return self._detail(submission, request)

        link = f"/portal/submissions/{submission.pk}"
        with transaction.atomic():
            before = snapshot(submission)
            submission.status = "RETURNED"
            submission.feedback_published_at = timezone.now()
            submission.save()
            record_change(
                request.user, submission, before, snapshot(submission),
                action="submission.feedback_published", request=request,
            )
            notify_user(
                submission.learner.user,
                "Teacher feedback available",
                "Your teacher has reviewed your work. Open the assignment to see "
                "the feedback and suggestions.",
                "ACADEMIC",
                link,
            )
            seen = set()
            guardians = LearnerGuardian.objects.filter(
                learner=submission.learner,
                is_verified=True,
                can_view_academics=True,
            ).select_related("guardian__user")
            for guardian_link in guardians:
                guardian_user = guardian_link.guardian.user
                if guardian_user.pk in seen:
                    continue
                seen.add(guardian_user.pk)
                notify_user(
                    guardian_user,
                    "Teacher feedback available",
                    "New teacher feedback has been shared for "
                    f"{submission.learner.user.full_name}. Sign in to view the "
                    "available information.",
                    "ACADEMIC",
                    link,
                )
        return self._detail(submission, request)

    @action(detail=True, methods=["post"], url_path="resubmit", url_name="resubmit")
    def resubmit(self, request, pk=None):
        submission = self.get_object()
        if not is_staff_user(request.user) and submission.learner.user_id != request.user.pk:
            raise PermissionDenied("Only the learner who owns this work may resubmit it.")
        serializer = ResubmitSerializer(
            data=request.data, context={"submission": submission, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        new_answer = serializer.validated_data.get("text_answer", "")
        new_attachment = serializer.validated_data.get("attachment", submission.attachment)
        with transaction.atomic():
            before = snapshot(submission)
            if not submission.attempts.exists():
                SubmissionAttempt.objects.create(
                    institution=submission.institution,
                    submission=submission,
                    attempt_number=submission.current_attempt,
                    text_answer=submission.text_answer,
                    attachment=submission.attachment,
                    score=submission.score,
                    feedback=submission.feedback,
                    graded_at=submission.graded_at,
                )
            next_attempt = submission.current_attempt + 1
            SubmissionAttempt.objects.create(
                institution=submission.institution,
                submission=submission,
                attempt_number=next_attempt,
                text_answer=new_answer,
                attachment=new_attachment,
            )
            submission.text_answer = new_answer
            submission.attachment = new_attachment
            submission.current_attempt = next_attempt
            submission.status = "SUBMITTED"
            submission.score = None
            submission.feedback = ""
            submission.graded_by = None
            submission.graded_at = None
            submission.rubric_level = None
            submission.rubric_level_name = ""
            submission.rubric_max_score = None
            submission.feedback_published_at = None
            submission.save()
            record_change(
                request.user, submission, before, snapshot(submission),
                action="submission.resubmitted", request=request,
            )
            teacher = submission.assignment.created_by
            if teacher is None and submission.assignment.course.teacher_id:
                teacher = submission.assignment.course.teacher.user
            notify_user(
                teacher,
                "Assignment submission received",
                f"{submission.learner.user.full_name} has submitted the assignment "
                f"\"{submission.assignment.title}\". It is now available for review.",
                "ACADEMIC",
                f"/admin/submissions/{submission.pk}",
            )
        return self._detail(submission, request)
