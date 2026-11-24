"""Assessment routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.assessments import views

router = DefaultRouter()
router.register("questions", views.QuestionViewSet, basename="question")
router.register("quizzes", views.QuizViewSet, basename="quiz")
router.register("quiz-questions", views.QuizQuestionViewSet, basename="quizquestion")
router.register("attempts", views.QuizAttemptViewSet, basename="quizattempt")
router.register("exams", views.ExamViewSet, basename="exam")
router.register("results", views.ExamResultViewSet, basename="examresult")

urlpatterns = [path("", include(router.urls))]
