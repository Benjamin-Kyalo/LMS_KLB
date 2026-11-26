"""Assessment serializers."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.assessments.models import (
    Answer, Exam, ExamResult, Question, Quiz, QuizAttempt, QuizQuestion,
)


class QuestionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ["institution", "created_by"]


class StudentQuestionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """Question shape for learners: no answer key or teacher explanation."""

    class Meta:
        model = Question
        fields = [
            "id", "institution", "subject", "learning_outcome", "question_type",
            "text", "options", "marks", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["institution", "created_by"]


class QuizQuestionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)

    class Meta:
        model = QuizQuestion
        fields = "__all__"


class QuizSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="quiz_questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = "__all__"
        read_only_fields = ["institution"]


class AnswerSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class QuizAttemptSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = "__all__"
        read_only_fields = [
            "institution", "quiz", "learner", "max_score", "started_at",
            "score", "completed_at", "status",
        ]


class QuizAnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer = serializers.CharField(allow_blank=True)


class QuizSubmissionSerializer(serializers.Serializer):
    """Accepts a batch of answers and marks objective questions automatically."""

    attempt = serializers.IntegerField()
    answers = QuizAnswerInputSerializer(many=True)


class ExamSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Exam
        fields = "__all__"
        read_only_fields = ["institution"]


class ExamResultSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)

    class Meta:
        model = ExamResult
        fields = "__all__"
        read_only_fields = ["institution", "recorded_by"]
