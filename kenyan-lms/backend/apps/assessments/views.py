"""Assessment API endpoints."""
from decimal import Decimal

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assessments.models import Answer, Exam, ExamResult, Question, Quiz, QuizAttempt, QuizQuestion
from apps.assessments.serializers import (
    AnswerSerializer, ExamResultSerializer, ExamSerializer, QuestionSerializer,
    QuizAttemptSerializer, QuizQuestionSerializer, QuizSerializer, QuizSubmissionSerializer,
)
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin


class QuestionViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Question.objects.select_related("subject", "learning_outcome")
    serializer_class = QuestionSerializer
    filterset_fields = ["question_type", "subject", "learning_outcome"]
    search_fields = ["text"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, created_by=self.request.user)


class QuizViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Quiz.objects.select_related("course", "subject")
    serializer_class = QuizSerializer
    filterset_fields = ["is_published", "course", "subject"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class QuizQuestionViewSet(StaffWriteMixin, viewsets.ModelViewSet):
    queryset = QuizQuestion.objects.select_related("question", "quiz")
    serializer_class = QuizQuestionSerializer
    filterset_fields = ["quiz"]


class QuizAttemptViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    filterset_fields = ["quiz", "learner", "status"]

    def perform_create(self, serializer):
        quiz = Quiz.objects.get(pk=serializer.validated_data["quiz"].pk)
        max_score = sum(q.marks for q in quiz.quiz_questions.all())
        serializer.save(institution=self.request.user.institution, max_score=max_score)

    @action(detail=False, methods=["post"], url_path="submit")
    def submit_attempt(self, request):
        """Mark objective answers, store subjective ones for teacher marking."""
        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = QuizAttempt.objects.get(
            pk=serializer.validated_data["attempt"],
            institution=request.user.institution,
        )
        total = Decimal("0")
        for item in serializer.validated_data["answers"]:
            question = Question.objects.get(pk=item["question"])
            correct = str(item["answer"]).strip().lower() == str(question.correct_answer).strip().lower()
            marks = question.marks if question.question_type in {"MCQ", "TRUE_FALSE"} and correct else Decimal("0")
            total += marks
            Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={"answer_text": str(item["answer"]), "is_correct": correct, "marks_obtained": marks},
            )
        attempt.score = total
        attempt.completed_at = timezone.now()
        attempt.status = "COMPLETED"
        attempt.save()
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_200_OK)


class ExamViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Exam.objects.select_related("subject", "school_class", "term")
    serializer_class = ExamSerializer
    filterset_fields = ["subject", "school_class", "term", "academic_year"]


class ExamResultViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ExamResult.objects.select_related("learner__user", "exam")
    serializer_class = ExamResultSerializer
    filterset_fields = ["exam", "learner", "grade"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, recorded_by=self.request.user)
