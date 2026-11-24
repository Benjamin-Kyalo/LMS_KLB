"""Curriculum serializers."""
from rest_framework import serializers

from apps.curriculum.models import (
    Competency, CompetencyEvidence, CurriculumFramework, EducationLevel,
    LearningArea, LearningOutcome, Rubric, RubricLevel, Strand, SubStrand,
)


class CurriculumFrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurriculumFramework
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class EducationLevelSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source="framework.name", read_only=True)

    class Meta:
        model = EducationLevel
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class LearningAreaSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source="level.name", read_only=True)

    class Meta:
        model = LearningArea
        fields = "__all__"


class StrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strand
        fields = "__all__"


class SubStrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubStrand
        fields = "__all__"


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"


class RubricLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubricLevel
        fields = "__all__"


class RubricSerializer(serializers.ModelSerializer):
    levels = RubricLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Rubric
        fields = "__all__"


class CompetencyEvidenceSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True)

    class Meta:
        model = CompetencyEvidence
        fields = "__all__"
        read_only_fields = ["recorded_by", "recorded_at", "institution"]
