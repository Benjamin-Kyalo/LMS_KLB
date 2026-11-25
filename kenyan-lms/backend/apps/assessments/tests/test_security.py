"""Focused integrity tests for question keys, link scoping and attempt submission."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessments.models import Answer, Question, Quiz, QuizAttempt, QuizQuestion
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()
PASSWORD = "StrongPass123!"


class AssessmentSecurityTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="SEC")
        self.school = Institution.objects.create(name="A", code="SEC-A", institution_type=kind)
        self.other = Institution.objects.create(name="B", code="SEC-B", institution_type=kind)

        self.admin = User.objects.create_user(
            username="sec-admin", password=PASSWORD,
            role=Roles.ADMIN, institution=self.school,
        )
        self.other_admin = User.objects.create_user(
            username="sec-admin-b", password=PASSWORD,
            role=Roles.ADMIN, institution=self.other,
        )
        self.platform = User.objects.create_user(
            username="sec-platform", password=PASSWORD, role=Roles.SUPER_ADMIN,
        )

        learner_user = User.objects.create_user(
            username="sec-learner", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="SEC-L1",
        )
        peer_user = User.objects.create_user(
            username="sec-learner-peer", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.peer_learner = Learner.objects.create(
            user=peer_user, institution=self.school, admission_number="SEC-L2",
        )
        foreign_user = User.objects.create_user(
            username="sec-learner-b", password=PASSWORD,
            role=Roles.LEARNER, institution=self.other,
        )
        self.foreign_learner = Learner.objects.create(
            user=foreign_user, institution=self.other, admission_number="SEC-B1",
        )

        self.quiz = Quiz.objects.create(
            institution=self.school, title="Quiz A", is_published=True,
        )
        self.question = Question.objects.create(
            institution=self.school, question_type="MCQ", text="2+2?",
            options=["3", "4", "5"], correct_answer="4",
            explanation="Two plus two is four.", marks=Decimal("2"),
        )
        self.link = QuizQuestion.objects.create(
            quiz=self.quiz, question=self.question, marks=Decimal("2"),
        )

        self.other_quiz = Quiz.objects.create(
            institution=self.school, title="Quiz A2", is_published=True,
        )
        self.other_question = Question.objects.create(
            institution=self.school, question_type="MCQ", text="3+3?",
            correct_answer="6", marks=Decimal("1"),
        )
        QuizQuestion.objects.create(
            quiz=self.other_quiz, question=self.other_question, marks=Decimal("1"),
        )

        self.foreign_quiz = Quiz.objects.create(
            institution=self.other, title="Quiz B", is_published=True,
        )
        self.foreign_question = Question.objects.create(
            institution=self.other, question_type="MCQ", text="9-4?",
            correct_answer="5", marks=Decimal("3"),
        )
        self.foreign_link = QuizQuestion.objects.create(
            quiz=self.foreign_quiz, question=self.foreign_question, marks=Decimal("3"),
        )

    @staticmethod
    def _results(response):
        return response.data["results"] if isinstance(response.data, dict) else response.data

    # H-2a: answer keys stay staff-only on every read path.
    def test_learner_question_reads_hide_answer_key(self):
        self.client.force_authenticate(user=self.learner.user)
        detail_url = reverse("question-detail", args=[self.question.id])
        for url in (
            reverse("question-list"),
            reverse("question-list") + "?search=2%2B2",
            detail_url,
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            payload = (
                response.data if url == detail_url
                else next(row for row in self._results(response) if row["id"] == self.question.id)
            )
            self.assertEqual(payload["text"], "2+2?")
            self.assertNotIn("correct_answer", payload)
            self.assertNotIn("explanation", payload)

    def test_staff_and_platform_question_reads_keep_answer_key(self):
        detail_url = reverse("question-detail", args=[self.question.id])
        for user in (self.admin, self.platform):
            self.client.force_authenticate(user=user)
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(response.data["correct_answer"], "4")
            self.assertEqual(response.data["explanation"], "Two plus two is four.")

    # H-2b: quiz/question links are scoped through the quiz's institution.
    def test_school_a_cannot_read_or_change_school_b_links(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("quizquestion-list"))
        self.assertCountEqual(
            [row["id"] for row in self._results(response)],
            [self.link.id, QuizQuestion.objects.get(quiz=self.other_quiz).id],
        )
        self.assertNotIn(
            self.foreign_link.id,
            [row["id"] for row in self._results(response)],
        )

        detail_url = reverse("quizquestion-detail", args=[self.foreign_link.id])
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {"sequence": 9}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(QuizQuestion.objects.filter(pk=self.foreign_link.id).exists())

    def test_link_writes_reject_foreign_quiz_or_question(self):
        self.client.force_authenticate(user=self.admin)
        list_url = reverse("quizquestion-list")
        for payload in (
            {"quiz": self.foreign_quiz.id, "question": self.question.id},
            {"quiz": self.quiz.id, "question": self.foreign_question.id},
        ):
            response = self.client.post(list_url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        detail_url = reverse("quizquestion-detail", args=[self.link.id])
        for field, value in (
            ("quiz", self.foreign_quiz.id),
            ("question", self.foreign_question.id),
        ):
            response = self.client.patch(detail_url, {field: value}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_platform_admin_retains_global_link_access(self):
        self.client.force_authenticate(user=self.platform)
        response = self.client.get(reverse("quizquestion-detail", args=[self.foreign_link.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        response = self.client.post(reverse("quizquestion-list"), {
            "quiz": self.foreign_quiz.id,
            "question": self.question.id,
            "sequence": 2,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    # H-3c: submission is ownership-, quiz- and institution-scoped.
    def test_learner_cannot_submit_another_learners_attempt(self):
        own = QuizAttempt.objects.create(
            institution=self.school, quiz=self.quiz, learner=self.learner,
        )
        peer = QuizAttempt.objects.create(
            institution=self.school, quiz=self.quiz, learner=self.peer_learner,
        )
        self.client.force_authenticate(user=self.learner.user)

        listing = self.client.get(reverse("quizattempt-list"))
        self.assertEqual([row["id"] for row in self._results(listing)], [own.id])

        payload = {
            "attempt": peer.id,
            "answers": [{"question": self.question.id, "answer": "4"}],
        }
        response = self.client.post("/api/assessments/attempts/submit/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        peer.refresh_from_db()
        self.assertEqual(peer.status, "IN_PROGRESS")

        payload["attempt"] = own.id
        response = self.client.post("/api/assessments/attempts/submit/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        own.refresh_from_db()
        self.assertEqual(own.score, Decimal("2"))

    def test_submit_rejects_questions_outside_attempt_quiz_or_institution(self):
        attempt = QuizAttempt.objects.create(
            institution=self.school, quiz=self.quiz, learner=self.learner,
        )
        self.client.force_authenticate(user=self.learner.user)
        for question_id in (self.other_question.id, self.foreign_question.id):
            response = self.client.post("/api/assessments/attempts/submit/", {
                "attempt": attempt.id,
                "answers": [{"question": question_id, "answer": "6"}],
            }, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "IN_PROGRESS")
        self.assertFalse(Answer.objects.filter(attempt=attempt).exists())

    def test_submit_rejects_already_completed_attempt(self):
        attempt = QuizAttempt.objects.create(
            institution=self.school, quiz=self.quiz, learner=self.learner,
            status="COMPLETED",
        )
        self.client.force_authenticate(user=self.learner.user)
        response = self.client.post("/api/assessments/attempts/submit/", {
            "attempt": attempt.id,
            "answers": [{"question": self.question.id, "answer": "4"}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertFalse(Answer.objects.filter(attempt=attempt).exists())

    def test_attempt_create_derives_ownership_and_integrity_fields(self):
        self.client.force_authenticate(user=self.learner.user)
        response = self.client.post(reverse("quizattempt-list"), {
            "quiz": self.quiz.id,
            "learner": self.peer_learner.id,
            "institution": self.other.id,
            "max_score": 999,
            "score": 999,
            "status": "COMPLETED",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        attempt = QuizAttempt.objects.get(pk=response.data["id"])
        self.assertEqual(attempt.quiz_id, self.quiz.id)
        self.assertEqual(attempt.learner_id, self.learner.id)
        self.assertEqual(attempt.institution_id, self.school.id)
        self.assertEqual(attempt.max_score, Decimal("2"))
        self.assertIsNone(attempt.score)
        self.assertEqual(attempt.status, "IN_PROGRESS")
