"""Curriculum serializers."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.curriculum.models import (
    Competency, CompetencyEvidence, CurriculumFramework, EducationLevel,
    FeedbackComment, LearningArea, LearningOutcome, Rubric, RubricCriterion,
    RubricLevel, Strand, SubStrand,
)


class CurriculumFrameworkSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = CurriculumFramework
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class EducationLevelSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    framework_name = serializers.CharField(source="framework.name", read_only=True)

    class Meta:
        model = EducationLevel
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class LearningAreaSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    level_name = serializers.CharField(source="level.name", read_only=True)

    class Meta:
        model = LearningArea
        fields = "__all__"


class StrandSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Strand
        fields = "__all__"


class SubStrandSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = SubStrand
        fields = "__all__"


class LearningOutcomeSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class CompetencySerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = "__all__"


class RubricLevelSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = RubricLevel
        fields = "__all__"

    def validate(self, attrs):
        min_score = attrs.get("min_score")
        max_score = attrs.get("max_score")
        if self.instance is not None:
            if min_score is None:
                min_score = self.instance.min_score
            if max_score is None:
                max_score = self.instance.max_score
        if min_score < 0 or max_score > 100:
            raise serializers.ValidationError(
                "Achievement bands use percentages from 0 to 100."
            )
        if min_score > max_score:
            raise serializers.ValidationError(
                "The minimum score cannot be greater than the maximum score."
            )
        return attrs


class RubricCriterionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = RubricCriterion
        fields = "__all__"

    def validate_max_score(self, value):
        if value <= 0:
            raise serializers.ValidationError("A criterion must allow a positive score.")
        return value


class RubricSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    levels = RubricLevelSerializer(many=True, read_only=True)
    criteria = RubricCriterionSerializer(many=True, read_only=True)

    class Meta:
        model = Rubric
        fields = "__all__"


class FeedbackCommentSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = FeedbackComment
        fields = "__all__"
        read_only_fields = ["created_by"]

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Write a comment before saving it.")
        return value


class CompetencyEvidenceSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True)

    class Meta:
        model = CompetencyEvidence
        fields = "__all__"
        read_only_fields = ["recorded_by", "recorded_at", "institution"]
