"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.tutor.models import TutorConversation, TutorMessage
from apps.tutor.scoping import validate_learner_choice
from apps.tutor.service import (
    MAX_QUESTION_LENGTH, clean_question, format_source, policy_metadata,
)


class TutorConversationSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """Conversations expose generated references and ids, never personal data."""

    class Meta:
        model = TutorConversation
        fields = "__all__"
        read_only_fields = [
            "id", "reference", "institution", "started_by", "created_at", "updated_at",
        ]

    def _target_institution_id(self):
        request = self.context.get("request")
        if request is None:
            return getattr(self.instance, "institution_id", None)
        data = getattr(request, "data", None)
        if isinstance(data, dict) and data.get("institution"):
            return data["institution"]
        if getattr(request.user, "institution_id", None):
            return request.user.institution_id
        return getattr(self.instance, "institution_id", None)

    def validate_learner(self, value):
        institution_id = self._target_institution_id()
        if value is not None and institution_id is not None:
            if str(value.institution_id) != str(institution_id):
                raise serializers.ValidationError("Choose a learner from this institution.")
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            return validate_learner_choice(user, value)
        return value


class TutorMessageSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """History records with human-readable, label-only source descriptions."""

    answer = serializers.CharField(source="body", read_only=True)
    source_labels = serializers.SerializerMethodField()
    conversation_title = serializers.CharField(source="conversation.title", read_only=True)
    grounded = serializers.SerializerMethodField()
    policy = serializers.SerializerMethodField()

    class Meta:
        model = TutorMessage
        fields = [
            "id", "reference", "institution", "conversation", "conversation_title",
            "role", "body", "answer", "sources", "source_labels", "suggestions", "grounded",
            "policy", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "reference", "institution", "created_by", "created_at", "updated_at",
        ]

    def get_source_labels(self, obj):
        return [
            formatted for source in (obj.sources or [])
            if (formatted := format_source(source))
        ]

    def get_grounded(self, obj):
        return bool(obj.sources)

    def get_policy(self, obj):
        return policy_metadata()


class AskQuestionSerializer(serializers.Serializer):
    """The only accepted shape for the ``ask`` action body."""

    question = serializers.CharField(
        trim_whitespace=True,
        max_length=MAX_QUESTION_LENGTH,
    )

    def to_internal_value(self, data):
        # DRF rejects control characters before field validators run. Clean
        # first so the same rule applies to every client, then validate length.
        if isinstance(data, dict) and "question" in data:
            data = {**data, "question": clean_question(data["question"])}
        return super().to_internal_value(data)
