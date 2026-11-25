"""Assessment API endpoints."""
from decimal import Decimal

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.assessments.models import Answer, Exam, ExamResult, Question, Quiz, QuizAttempt, QuizQuestion
from apps.assessments.serializers import (
    AnswerSerializer, ExamResultSerializer, ExamSerializer, QuestionSerializer,
    QuizAttemptSerializer, QuizQuestionSerializer, QuizSerializer, QuizSubmissionSerializer,
    StudentQuestionSerializer,
)
from apps.core.constants import Capabilities
from apps.core.permissions import is_platform_admin, is_staff_user, same_institution
from apps.core.viewsets import InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.learners.models import Learner


def _is_staff(user):
    """Match the staff rule used by StaffWriteMixin."""
    return is_staff_user(user)


class QuestionViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ASSESSMENTS_MANAGE
    queryset = Question.objects.select_related("subject", "learning_outcome")
    serializer_class = QuestionSerializer
    filterset_fields = ["question_type", "subject", "learning_outcome"]
    search_fields = ["text"]

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"} and not _is_staff(self.request.user):
            return StudentQuestionSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, created_by=self.request.user)


class QuizViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ASSESSMENTS_MANAGE
    queryset = Quiz.objects.select_related("course", "subject")
    serializer_class = QuizSerializer
    filterset_fields = ["is_published", "course", "subject"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class QuizQuestionViewSet(StaffWriteMixin, viewsets.ModelViewSet):
    capability = Capabilities.ASSESSMENTS_MANAGE
    queryset = QuizQuestion.objects.select_related("question", "quiz")
    serializer_class = QuizQuestionSerializer
    filterset_fields = ["quiz"]

    def get_queryset(self):
        queryset = self.queryset.all()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if is_platform_admin(user):
            return queryset
        if user.institution_id:
            return queryset.filter(quiz__institution_id=user.institution_id)
        return queryset.none()

    def _validate_related_institution(self, quiz, question):
        user = self.request.user
        if not same_institution(user, quiz.institution_id) or not same_institution(user, question.institution_id):
            raise ValidationError("The quiz and question must belong to your institution.")

    def perform_create(self, serializer):
        validated = serializer.validated_data
        self._validate_related_institution(validated["quiz"], validated["question"])
        serializer.save()

    def perform_update(self, serializer):
        quiz = serializer.validated_data.get("quiz", serializer.instance.quiz)
        question = serializer.validated_data.get("question", serializer.instance.question)
        self._validate_related_institution(quiz, question)
        serializer.save()


class QuizAttemptViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    filterset_fields = ["quiz", "learner", "status"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not _is_staff(user):
            return queryset.filter(learner__user=user)
        return queryset

    def _own_learner(self, user):
        learner = getattr(user, "learner_profile", None)
        if learner is None:
            raise ValidationError("Your account is not linked to a learner profile.")
        return learner

    def _resolve_quiz(self, quiz_id):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except (Quiz.DoesNotExist, ValueError, TypeError) as exc:
            raise ValidationError({"quiz": "Choose a valid quiz."}) from exc
        if not same_institution(self.request.user, quiz.institution_id):
            raise ValidationError({"quiz": "Choose a quiz from your institution."})
        return quiz

    def _resolve_learner(self, learner_id):
        try:
            learner = Learner.objects.get(pk=learner_id)
        except (Learner.DoesNotExist, ValueError, TypeError) as exc:
            raise ValidationError({"learner": "Choose a valid learner."}) from exc
        if not same_institution(self.request.user, learner.institution_id):
            raise ValidationError({"learner": "Choose a learner from your institution."})
        return learner

    def perform_create(self, serializer):
        user = self.request.user
        quiz = self._resolve_quiz(self.request.data.get("quiz"))
        if _is_staff(user):
            learner = self._resolve_learner(self.request.data.get("learner"))
        else:
            learner = self._own_learner(user)
        max_score = sum(q.marks for q in quiz.quiz_questions.all())
        serializer.save(institution=quiz.institution, quiz=quiz, learner=learner, max_score=max_score)

    @action(detail=False, methods=["post"], url_path="submit")
    def submit_attempt(self, request):
        """Mark objective answers, store subjective ones for teacher marking."""
        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = get_object_or_404(
            self.get_queryset(), pk=serializer.validated_data["attempt"],
        )
        if attempt.status != "IN_PROGRESS":
            raise ValidationError({"attempt": "This attempt has already been completed."})
        allowed_questions = {
            question.pk: question
            for question in Question.objects.filter(
                institution_id=attempt.institution_id,
                quizquestion__quiz_id=attempt.quiz_id,
            )
        }
        total = Decimal("0")
        for item in serializer.validated_data["answers"]:
            question = allowed_questions.get(item["question"])
            if question is None:
                raise ValidationError({
                    "answers": f"Question {item['question']} is not part of this attempt.",
                })
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
    capability = Capabilities.ASSESSMENTS_MANAGE
    queryset = Exam.objects.select_related("subject", "school_class", "term")
    serializer_class = ExamSerializer
    filterset_fields = ["subject", "school_class", "term", "academic_year"]


class ExamResultViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ASSESSMENTS_MANAGE
    queryset = ExamResult.objects.select_related("learner__user", "exam")
    serializer_class = ExamResultSerializer
    filterset_fields = ["exam", "learner", "grade"]

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution, recorded_by=self.request.user)
