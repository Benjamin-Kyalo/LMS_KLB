"""Failed submissions must not leave partial records behind."""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from apps.assessments.models import Answer, Question, Quiz, QuizAttempt, QuizQuestion
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner
from apps.theming.models import SiteContent

User = get_user_model()


class AtomicWriteTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Atomic Primary", code="ATP")
        self.school = Institution.objects.create(
            name="Atomic School", code="ATSC", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="atomicadmin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school, is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_failed_teacher_creation_does_not_leave_a_user(self):
        payload = {
            "username": "broken_teacher",
            "first_name": "Broken",
            "last_name": "Teacher",
            "email": "broken.teacher@example.invalid",
            "password": "StrongPass123!",
            "role": Roles.TEACHER,
            "institution": self.school.pk,
        }
        with patch(
            "apps.accounts.serializers.TeacherApproval.objects.create",
            side_effect=RuntimeError("simulated failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("user-list"), payload, format="json")
        self.assertFalse(User.objects.filter(username="broken_teacher").exists())

    def test_failed_bulk_import_rolls_back_earlier_rows(self):
        csv_text = (
            "username,first_name,last_name,admission_number\n"
            "bulkone,Bulk,One,ATM001\n"
            "bulktwo,Bulk,Two,ATM002\n"
        )
        # Fail after the first row has been saved to prove the batch rolls back.
        from apps.learners.serializers import LearnerCreateSerializer

        real_learner_save = LearnerCreateSerializer.save
        calls = {"count": 0}

        def fail_on_second_learner(serializer):
            calls["count"] += 1
            if calls["count"] == 2:
                raise serializers.ValidationError("simulated import failure")
            return real_learner_save(serializer)

        with patch.object(LearnerCreateSerializer, "save", fail_on_second_learner):
            response = self.client.post(
                reverse("learner-bulk-import"), {"csv_text": csv_text}, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username__in=["bulkone", "bulktwo"]).exists())
        self.assertFalse(Learner.objects.filter(admission_number__in=["ATM001", "ATM002"]).exists())

    def test_invalid_quiz_submission_does_not_store_answers(self):
        learner_user = User.objects.create_user(
            username="atomiclearner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="ATL001"
        )
        quiz = Quiz.objects.create(institution=self.school, title="Atomic quiz")
        first = Question.objects.create(
            institution=self.school, question_type="MCQ", text="2+2?",
            options=["3", "4"], correct_answer="4", marks=Decimal("2"),
        )
        other = Question.objects.create(
            institution=self.school, question_type="MCQ", text="3+3?",
            options=["5", "6"], correct_answer="6", marks=Decimal("2"),
        )
        QuizQuestion.objects.create(quiz=quiz, question=first, marks=Decimal("2"))
        attempt = QuizAttempt.objects.create(
            institution=self.school, quiz=quiz, learner=learner
        )
        response = self.client.post("/api/assessments/attempts/submit/", {
            "attempt": attempt.pk,
            "answers": [
                {"question": first.pk, "answer": "4"},
                {"question": other.pk, "answer": "6"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Answer.objects.filter(attempt=attempt).exists())
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "IN_PROGRESS")

    def test_invalid_site_content_patch_does_not_create_a_row(self):
        self.assertEqual(SiteContent.objects.count(), 0)
        response = self.client.patch(reverse("site-content"), {
            "content": {"styles": {"hero": {"background": "url(javascript:alert(1))"}}},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SiteContent.objects.count(), 0)
