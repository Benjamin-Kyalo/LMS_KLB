"""Curriculum API endpoints."""
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.core.audit import log_audit, record_change, snapshot
from apps.core.constants import Capabilities
from apps.core.permissions import is_platform_admin, staff_or_capability_permission
from apps.core.viewsets import (
    READ_ACTIONS, InstitutionScopedQuerysetMixin, PlatformWriteMixin, StaffWriteMixin,
)
from apps.curriculum.models import (
    Competency, CompetencyEvidence, CurriculumFramework, EducationLevel,
    FeedbackComment, LearningArea, LearningOutcome, Rubric, RubricCriterion,
    RubricLevel, Strand, SubStrand,
)
from apps.curriculum.serializers import (
    CompetencyEvidenceSerializer, CompetencySerializer, CurriculumFrameworkSerializer,
    EducationLevelSerializer, FeedbackCommentSerializer, LearningAreaSerializer,
    LearningOutcomeSerializer, RubricCriterionSerializer, RubricLevelSerializer,
    RubricSerializer, StrandSerializer, SubStrandSerializer,
)


class CurriculumFrameworkViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = CurriculumFramework.objects.all()
    serializer_class = CurriculumFrameworkSerializer
    filterset_fields = ["is_active"]


class EducationLevelViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = EducationLevel.objects.select_related("framework")
    serializer_class = EducationLevelSerializer
    filterset_fields = ["framework"]


class LearningAreaViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = LearningArea.objects.select_related("level")
    serializer_class = LearningAreaSerializer
    filterset_fields = ["level"]
    search_fields = ["name"]


class StrandViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = Strand.objects.select_related("learning_area")
    serializer_class = StrandSerializer
    filterset_fields = ["learning_area"]


class SubStrandViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = SubStrand.objects.select_related("strand")
    serializer_class = SubStrandSerializer
    filterset_fields = ["strand"]


class LearningOutcomeViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = LearningOutcome.objects.select_related("sub_strand")
    serializer_class = LearningOutcomeSerializer
    filterset_fields = ["sub_strand"]
    search_fields = ["code", "description"]


class CompetencyViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = Competency.objects.all()
    serializer_class = CompetencySerializer
    filterset_fields = ["framework"]


def _visible_rubrics(queryset, user):
    """Platform users see every rubric; schools see theirs plus global templates."""
    if is_platform_admin(user):
        return queryset
    if user.institution_id:
        return queryset.filter(
            Q(institution_id=user.institution_id) | Q(institution__isnull=True)
        )
    return queryset.filter(institution__isnull=True)


def _require_mutable_rubric(rubric, user):
    if rubric.institution_id is None and not is_platform_admin(user):
        raise PermissionDenied("Global rubric templates can only be changed by the platform administrator.")


class RubricWriteMixin:
    """Staff may build school rubrics; global templates stay platform-owned."""

    def get_permissions(self):
        if self.action in READ_ACTIONS:
            return [IsAuthenticated()]
        return [
            IsAuthenticated(),
            staff_or_capability_permission(Capabilities.ASSESSMENTS_MANAGE)(),
        ]

    def perform_create(self, serializer):
        rubric = serializer.validated_data.get("rubric")
        if rubric is not None:
            _require_mutable_rubric(rubric, self.request.user)
        super().perform_create(serializer)
        instance = serializer.instance
        institution_id = getattr(rubric, "institution_id", None) or getattr(instance, "institution_id", None)
        log_audit(
            self.request.user, "rubric.created", type(instance).__name__, instance.pk,
            snapshot(instance), institution=institution_id, request=self.request,
        )

    def perform_update(self, serializer):
        rubric = getattr(serializer.instance, "rubric", None) or serializer.instance
        _require_mutable_rubric(rubric, self.request.user)
        before = snapshot(serializer.instance)
        super().perform_update(serializer)
        institution_id = getattr(rubric, "institution_id", None) or getattr(serializer.instance, "institution_id", None)
        record_change(
            self.request.user, serializer.instance, before, snapshot(serializer.instance),
            action="rubric.updated", request=self.request, institution=institution_id,
        )

    def perform_destroy(self, instance):
        rubric = getattr(instance, "rubric", None) or instance
        _require_mutable_rubric(rubric, self.request.user)
        before = snapshot(instance)
        super().perform_destroy(instance)
        institution_id = getattr(rubric, "institution_id", None) or getattr(instance, "institution_id", None)
        log_audit(
            self.request.user, "rubric.deleted", type(instance).__name__, instance.pk,
            before, institution=institution_id, request=self.request,
        )


class RubricViewSet(RubricWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Rubrics may be global templates or school-specific."""

    serializer_class = RubricSerializer

    def get_queryset(self):
        return _visible_rubrics(
            Rubric.objects.prefetch_related("levels", "criteria"), self.request.user
        )


class RubricLevelViewSet(RubricWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RubricLevel.objects.select_related("rubric")
    serializer_class = RubricLevelSerializer
    filterset_fields = ["rubric"]

    def get_queryset(self):
        visible = _visible_rubrics(Rubric.objects.all(), self.request.user)
        return RubricLevel.objects.select_related("rubric").filter(rubric_id__in=visible.values("pk"))


class RubricCriterionViewSet(RubricWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RubricCriterion.objects.select_related("rubric")
    serializer_class = RubricCriterionSerializer
    filterset_fields = ["rubric"]

    def get_queryset(self):
        visible = _visible_rubrics(Rubric.objects.all(), self.request.user)
        return RubricCriterion.objects.select_related("rubric").filter(
            rubric_id__in=visible.values("pk")
        )


class FeedbackCommentViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Reusable feedback phrases, shared globally or owned by one school."""

    serializer_class = FeedbackCommentSerializer
    search_fields = ["text", "category"]

    def get_permissions(self):
        if self.action in READ_ACTIONS:
            return [IsAuthenticated()]
        return [
            IsAuthenticated(),
            staff_or_capability_permission(Capabilities.ASSESSMENTS_MANAGE)(),
        ]

    def get_queryset(self):
        qs = FeedbackComment.objects.select_related("created_by")
        if is_platform_admin(self.request.user):
            return qs
        if self.request.user.institution_id:
            return qs.filter(
                Q(institution_id=self.request.user.institution_id) | Q(institution__isnull=True)
            )
        return qs.filter(institution__isnull=True)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        super().perform_create(serializer)
        instance = serializer.instance
        log_audit(
            self.request.user, "feedback_comment.created", "FeedbackComment", instance.pk,
            {"text": instance.text, "category": instance.category},
            institution=instance.institution_id, request=self.request,
        )

    def perform_update(self, serializer):
        if serializer.instance.institution_id is None and not is_platform_admin(self.request.user):
            raise PermissionDenied("Global feedback comments can only be changed by the platform administrator.")
        before = snapshot(serializer.instance)
        super().perform_update(serializer)
        record_change(
            self.request.user, serializer.instance, before, snapshot(serializer.instance),
            action="feedback_comment.updated", request=self.request,
        )

    def perform_destroy(self, instance):
        if instance.institution_id is None and not is_platform_admin(self.request.user):
            raise PermissionDenied("Global feedback comments can only be changed by the platform administrator.")
        before = snapshot(instance)
        super().perform_destroy(instance)
        log_audit(
            self.request.user, "feedback_comment.deleted", "FeedbackComment", instance.pk,
            before, institution=instance.institution_id, request=self.request,
        )


class CompetencyEvidenceViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CompetencyEvidence.objects.select_related("learner__user", "outcome", "competency", "rubric_level")
    serializer_class = CompetencyEvidenceSerializer
    filterset_fields = ["learner", "outcome", "competency", "achieved_level", "evidence_type"]
    search_fields = ["learner__user__first_name", "learner__user__last_name", "notes"]

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            recorded_by=self.request.user,
        )
