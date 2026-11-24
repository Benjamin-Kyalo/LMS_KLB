"""Assessment serializers."""
from rest_framework import serializers

from apps.assessments.models import (
    Answer, Exam, ExamResult, Question, Quiz, QuizAttempt, QuizQuestion,
)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ["institution", "created_by"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)

    class Meta:
        model = QuizQuestion
        fields = "__all__"


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="quiz_questions.count", read_only=True)

    class Meta:
        model = Quiz
        fields = "__all__"
        read_only_fields = ["institution"]


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class QuizAttemptSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = "__all__"
        read_only_fields = ["institution", "started_at", "score", "completed_at", "status"]


class QuizSubmissionSerializer(serializers.Serializer):
    """Accepts a batch of answers and marks objective questions automatically."""

    attempt = serializers.IntegerField()
    answers = serializers.ListField(child=serializers.DictField())

    def validate_answers(self, value):
        for item in value:
            if "question" not in item or "answer" not in item:
                raise serializers.ValidationError("Each answer needs 'question' and 'answer'.")
        return value


class ExamSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Exam
        fields = "__all__"
        read_only_fields = ["institution"]


class ExamResultSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)

    class Meta:
        model = ExamResult
        fields = "__all__"
        read_only_fields = ["institution", "recorded_by"]
