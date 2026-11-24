"""Curriculum API endpoints."""
from rest_framework import viewsets

from apps.core.viewsets import InstitutionScopedQuerysetMixin, PlatformWriteMixin, StaffWriteMixin
from apps.curriculum.models import (
    Competency, CompetencyEvidence, CurriculumFramework, EducationLevel,
    LearningArea, LearningOutcome, Rubric, RubricLevel, Strand, SubStrand,
)
from apps.curriculum.serializers import (
    CompetencyEvidenceSerializer, CompetencySerializer, CurriculumFrameworkSerializer,
    EducationLevelSerializer, LearningAreaSerializer, LearningOutcomeSerializer,
    RubricLevelSerializer, RubricSerializer, StrandSerializer, SubStrandSerializer,
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


class RubricViewSet(PlatformWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """
    Rubrics may be global (institution=None) or school-specific.
    Platform admins see all; school users see their own plus global rubrics.
    """

    serializer_class = RubricSerializer

    def get_queryset(self):
        qs = Rubric.objects.prefetch_related("levels")
        user = self.request.user
        if user.is_platform_user:
            return qs
        if user.institution_id:
            return qs.filter(institution_id=user.institution_id) | qs.filter(institution__isnull=True)
        return qs.filter(institution__isnull=True)


class RubricLevelViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = RubricLevel.objects.select_related("rubric")
    serializer_class = RubricLevelSerializer
    filterset_fields = ["rubric"]


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
