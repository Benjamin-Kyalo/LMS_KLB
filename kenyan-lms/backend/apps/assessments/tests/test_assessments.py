"""Quiz auto-marking and result isolation tests."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessments.models import Question, Quiz, QuizAttempt, QuizQuestion
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


class QuizMarkingTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(name="A", code="A1", institution_type=kind)
        self.admin = User.objects.create_user(username="a", password="StrongPass123!", role=Roles.SCHOOL_ADMIN, institution=self.school)
        learner_user = User.objects.create_user(username="l", password="StrongPass123!", role=Roles.LEARNER, institution=self.school)
        self.learner = Learner.objects.create(user=learner_user, institution=self.school, admission_number="L1")
        self.quiz = Quiz.objects.create(institution=self.school, title="Q", is_published=True)
        self.q = Question.objects.create(
            institution=self.school, question_type="MCQ", text="2+2?",
            options=["3", "4", "5"], correct_answer="4", marks=Decimal("2"),
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.q, marks=Decimal("2"))

    def test_correct_answer_scores_marks(self):
        attempt = QuizAttempt.objects.create(institution=self.school, quiz=self.quiz, learner=self.learner)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/assessments/attempts/submit/", {
            "attempt": attempt.id,
            "answers": [{"question": self.q.id, "answer": "4"}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, Decimal("2"))
        self.assertEqual(attempt.status, "COMPLETED")

    def test_wrong_answer_scores_zero(self):
        attempt = QuizAttempt.objects.create(institution=self.school, quiz=self.quiz, learner=self.learner)
        self.client.force_authenticate(user=self.admin)
        self.client.post("/api/assessments/attempts/submit/", {
            "attempt": attempt.id,
            "answers": [{"question": self.q.id, "answer": "5"}],
        }, format="json")
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, Decimal("0"))
