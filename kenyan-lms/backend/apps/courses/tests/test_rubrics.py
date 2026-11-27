"""Criterion-based grading, feedback publication and resubmission workflow."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.communications.models import Notification
from apps.core.audit import AuditLog
from apps.core.constants import Roles
from apps.courses.models import Assignment, Course, Submission, SubmissionCriterionScore
from apps.curriculum.models import Rubric, RubricCriterion, RubricLevel
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()
PASSWORD = "StrongPass123!"


class RubricGradingTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="RBR")
        self.school = Institution.objects.create(
            name="Rubric School", code="RBR-A", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="rubric-admin", password=PASSWORD,
            role=Roles.ADMIN, institution=self.school,
        )

        learner_user = User.objects.create_user(
            username="rubric-learner", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="RBR-L1"
        )

        guardian_user = User.objects.create_user(
            username="rubric-guardian", password=PASSWORD,
            role=Roles.GUARDIAN, institution=self.school,
        )
        guardian = Guardian.objects.create(
            user=guardian_user, institution=self.school, guardian_number="RBR-G1"
        )
        LearnerGuardian.objects.create(
            learner=self.learner, guardian=guardian,
            is_verified=True, can_view_academics=True,
        )
        self.guardian_user = guardian_user

        private_guardian_user = User.objects.create_user(
            username="rubric-guardian-private", password=PASSWORD,
            role=Roles.GUARDIAN, institution=self.school,
        )
        private_guardian = Guardian.objects.create(
            user=private_guardian_user, institution=self.school,
            guardian_number="RBR-G2",
        )
        LearnerGuardian.objects.create(
            learner=self.learner, guardian=private_guardian,
            is_verified=True, can_view_academics=False,
        )
        self.private_guardian_user = private_guardian_user

        self.rubric = Rubric.objects.create(
            institution=self.school, name="Essay rubric", description="Writing assessment"
        )
        RubricLevel.objects.create(
            rubric=self.rubric, name="Beginning", min_score=Decimal("0"),
            max_score=Decimal("40"), sequence=1,
        )
        RubricLevel.objects.create(
            rubric=self.rubric, name="Developing", min_score=Decimal("50"),
            max_score=Decimal("70"), sequence=2,
        )
        RubricLevel.objects.create(
            rubric=self.rubric, name="Achieving", min_score=Decimal("80"),
            max_score=Decimal("100"), sequence=3,
        )
        self.criteria = [
            RubricCriterion.objects.create(
                rubric=self.rubric, name="Content", max_score=Decimal("5"), sequence=1
            ),
            RubricCriterion.objects.create(
                rubric=self.rubric, name="Language", max_score=Decimal("5"), sequence=2
            ),
        ]

        course = Course.objects.create(
            institution=self.school, title="English", status="PUBLISHED"
        )
        self.assignment = Assignment.objects.create(
            institution=self.school, course=course, title="Essay", max_score=Decimal("10"),
            rubric=self.rubric, allow_resubmission=True, max_attempts=2,
            is_published=True, created_by=self.admin,
        )
        self.submission = Submission.objects.create(
            institution=self.school, assignment=self.assignment,
            learner=self.learner, text_answer="First answer",
        )

    def _grade_payload(self):
        return {
            "criteria": [
                {"criterion": self.criteria[0].pk, "score": "4.00", "comment": "Clear point."},
                {"criterion": self.criteria[1].pk, "score": "5.00", "comment": "Strong wording."},
            ],
            "overall_feedback": "Good work overall.",
            "private_notes": "Check handwriting next time.",
        }

    def _grade(self):
        self.client.force_authenticate(user=self.admin)
        return self.client.post(
            reverse("submission-grade-rubric", args=[self.submission.pk]),
            self._grade_payload(), format="json",
        )

    def test_staff_can_grade_with_a_rubric_and_the_result_is_audited(self):
        response = self._grade()

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.score, Decimal("9.00"))
        self.assertEqual(self.submission.rubric_level_name, "Achieving")
        self.assertEqual(self.submission.status, "GRADED")
        self.assertEqual(
            SubmissionCriterionScore.objects.filter(submission=self.submission).count(), 2
        )
        self.assertTrue(
            AuditLog.objects.filter(action="submission.rubric_graded").exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(action="submission.rubric_scores").exists()
        )

    def test_learner_cannot_grade_and_private_notes_stay_hidden_until_publication(self):
        self._grade()
        self.client.force_authenticate(user=self.learner.user)

        detail = self.client.get(reverse("submission-detail", args=[self.submission.pk]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertNotIn("private_notes", detail.data)
        self.assertNotIn("score", detail.data)
        self.assertNotIn("feedback", detail.data)
        for row in detail.data["criterion_scores"]:
            self.assertNotIn("score", row)
            self.assertNotIn("comment", row)

        forbidden = self.client.post(
            reverse("submission-grade-rubric", args=[self.submission.pk]),
            self._grade_payload(), format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_publishing_feedback_notifies_the_learner_and_permitted_guardians(self):
        self._grade()
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("submission-publish-feedback", args=[self.submission.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "RETURNED")
        self.assertIsNotNone(self.submission.feedback_published_at)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.learner.user, notification_type="ACADEMIC"
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.guardian_user, notification_type="ACADEMIC"
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(recipient=self.private_guardian_user).exists()
        )

    def test_resubmission_keeps_the_old_attempt_and_clears_current_grade(self):
        self._grade()
        self.client.force_authenticate(user=self.learner.user)

        response = self.client.post(
            reverse("submission-resubmit", args=[self.submission.pk]),
            {"text_answer": "Improved answer"}, format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.current_attempt, 2)
        self.assertEqual(self.submission.text_answer, "Improved answer")
        self.assertEqual(self.submission.status, "SUBMITTED")
        self.assertIsNone(self.submission.score)
        attempts = list(self.submission.attempts.order_by("attempt_number"))
        self.assertEqual([row.attempt_number for row in attempts], [1, 2])
        self.assertEqual(attempts[0].score, Decimal("9.00"))
        self.assertIsNone(attempts[1].score)
        self.assertFalse(
            SubmissionCriterionScore.objects.filter(
                submission=self.submission, attempt_number=2
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(recipient=self.admin, title="Assignment submission received").exists()
        )

        second = self.client.post(
            reverse("submission-resubmit", args=[self.submission.pk]),
            {"text_answer": "One answer too many"}, format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criteria_from_another_institution_are_rejected(self):
        other_type = InstitutionType.objects.create(name="Other", code="RBX")
        other_school = Institution.objects.create(
            name="Other School", code="RBX-A", institution_type=other_type
        )
        other_rubric = Rubric.objects.create(institution=other_school, name="Foreign rubric")
        foreign = RubricCriterion.objects.create(
            rubric=other_rubric, name="Foreign criterion", max_score=Decimal("10")
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("submission-grade-rubric", args=[self.submission.pk]),
            {"criteria": [{"criterion": foreign.pk, "score": "5.00"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permitted_guardian_can_view_feedback_but_cannot_resubmit(self):
        self._grade()
        self.client.force_authenticate(user=self.admin)
        self.client.post(reverse("submission-publish-feedback", args=[self.submission.pk]))

        self.client.force_authenticate(user=self.guardian_user)
        detail = self.client.get(reverse("submission-detail", args=[self.submission.pk]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["score"], "9.00")
        self.assertEqual(detail.data["rubric_name"], "Essay rubric")
        self.assertEqual(detail.data["achievement_level"], "Achieving")
        self.assertEqual(detail.data["assignment_max_score"], "10.00")

        denied = self.client.post(
            reverse("submission-resubmit", args=[self.submission.pk]),
            {"text_answer": "Guardian attempt"}, format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.private_guardian_user)
        hidden = self.client.get(reverse("submission-detail", args=[self.submission.pk]))
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)
