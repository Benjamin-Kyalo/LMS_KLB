"""Focused tests for submission ownership, grading and progress integrity."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.courses.models import (
    Assignment, Course, Lesson, LessonProgress, Module, Submission,
)
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()
PASSWORD = "StrongPass123!"


class CourseSecurityTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="CRS")
        self.school = Institution.objects.create(name="A", code="CRS-A", institution_type=kind)
        self.other = Institution.objects.create(name="B", code="CRS-B", institution_type=kind)

        self.admin = User.objects.create_user(
            username="crs-admin", password=PASSWORD,
            role=Roles.ADMIN, institution=self.school,
        )
        self.other_admin = User.objects.create_user(
            username="crs-admin-b", password=PASSWORD,
            role=Roles.ADMIN, institution=self.other,
        )

        learner_user = User.objects.create_user(
            username="crs-learner", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="CRS-L1",
        )
        peer_user = User.objects.create_user(
            username="crs-learner-peer", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.peer_learner = Learner.objects.create(
            user=peer_user, institution=self.school, admission_number="CRS-L2",
        )
        foreign_user = User.objects.create_user(
            username="crs-learner-b", password=PASSWORD,
            role=Roles.LEARNER, institution=self.other,
        )
        self.foreign_learner = Learner.objects.create(
            user=foreign_user, institution=self.other, admission_number="CRS-B1",
        )

        self.course = Course.objects.create(
            institution=self.school, title="Maths", status="PUBLISHED",
        )
        self.module = Module.objects.create(
            institution=self.school, course=self.course, title="M1",
        )
        self.lesson = Lesson.objects.create(
            institution=self.school, module=self.module, title="L1",
        )

        foreign_course = Course.objects.create(
            institution=self.other, title="Science", status="PUBLISHED",
        )
        foreign_module = Module.objects.create(
            institution=self.other, course=foreign_course, title="M2",
        )
        self.foreign_lesson = Lesson.objects.create(
            institution=self.other, module=foreign_module, title="L2",
        )

        self.assignment = Assignment.objects.create(
            institution=self.school, course=self.course, title="A1",
            max_score=Decimal("10"), is_published=True, created_by=self.admin,
        )
        self.second_assignment = Assignment.objects.create(
            institution=self.school, course=self.course, title="A2",
            max_score=Decimal("20"), is_published=True, created_by=self.admin,
        )
        self.submission = Submission.objects.create(
            institution=self.school, assignment=self.assignment,
            learner=self.learner, text_answer="mine",
        )
        self.peer_submission = Submission.objects.create(
            institution=self.school, assignment=self.assignment,
            learner=self.peer_learner, text_answer="peer",
        )

    @staticmethod
    def _results(response):
        return response.data["results"] if isinstance(response.data, dict) else response.data

    # H-3a: learner submission access is object-owned, staff is institution-wide.
    def test_learner_sees_only_own_submissions_and_create_derives_learner(self):
        self.client.force_authenticate(user=self.learner.user)

        listing = self.client.get(reverse("submission-list"))
        self.assertEqual([row["id"] for row in self._results(listing)], [self.submission.id])
        peer_url = reverse("submission-detail", args=[self.peer_submission.id])
        self.assertEqual(self.client.get(peer_url).status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(reverse("submission-list"), {
            "assignment": self.second_assignment.id,
            "text_answer": "new answer",
            "institution": self.other.id,
            "score": 20,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = Submission.objects.get(pk=response.data["id"])
        self.assertEqual(created.learner_id, self.learner.id)
        self.assertEqual(created.institution_id, self.school.id)
        self.assertIsNone(created.score)

    def test_learner_patch_cannot_set_grade_fields_or_move_submission(self):
        self.client.force_authenticate(user=self.learner.user)
        detail_url = reverse("submission-detail", args=[self.submission.id])

        response = self.client.patch(detail_url, {
            "text_answer": "edited",
            "status": "DRAFT",
            "assignment": self.second_assignment.id,
            "score": 99,
            "feedback": "forged",
            "graded_by": self.admin.id,
            "graded_at": "2020-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.text_answer, "edited")
        self.assertEqual(self.submission.status, "DRAFT")
        self.assertEqual(self.submission.assignment_id, self.assignment.id)
        self.assertIsNone(self.submission.score)
        self.assertEqual(self.submission.feedback, "")
        self.assertIsNone(self.submission.graded_by_id)
        self.assertIsNone(self.submission.graded_at)

        response = self.client.patch(detail_url, {"status": "GRADED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "DRAFT")

    def test_learner_cannot_grade_or_patch_peer_submission(self):
        self.client.force_authenticate(user=self.learner.user)
        grade_url = f"/api/courses/submissions/{self.submission.id}/grade/"
        response = self.client.post(grade_url, {"score": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        peer_url = reverse("submission-detail", args=[self.peer_submission.id])
        response = self.client.patch(peer_url, {"text_answer": "stolen"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)
        self.peer_submission.refresh_from_db()
        self.assertEqual(self.peer_submission.text_answer, "peer")

    def test_staff_access_is_institution_wide(self):
        self.client.force_authenticate(user=self.admin)
        listing = self.client.get(reverse("submission-list"))
        self.assertCountEqual(
            [row["id"] for row in self._results(listing)],
            [self.submission.id, self.peer_submission.id],
        )

        self.client.force_authenticate(user=self.other_admin)
        own_url = reverse("submission-detail", args=[self.submission.id])
        self.assertEqual(self.client.get(own_url).status_code, status.HTTP_404_NOT_FOUND)
        grade_url = f"/api/courses/submissions/{self.submission.id}/grade/"
        self.assertEqual(
            self.client.post(grade_url, {"score": 5}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # H-3b: grade scores are validated and grading metadata is server-owned.
    def test_grade_rejects_non_numeric_negative_and_over_max_scores(self):
        self.client.force_authenticate(user=self.admin)
        grade_url = f"/api/courses/submissions/{self.submission.id}/grade/"
        for score in ("abc", -1, 11):
            response = self.client.post(grade_url, {"score": score}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        self.submission.refresh_from_db()
        self.assertIsNone(self.submission.score)
        self.assertEqual(self.submission.status, "SUBMITTED")
        self.assertIsNone(self.submission.graded_by_id)

    def test_grade_accepts_valid_score_and_sets_server_fields(self):
        self.client.force_authenticate(user=self.admin)
        grade_url = f"/api/courses/submissions/{self.submission.id}/grade/"
        response = self.client.post(
            grade_url, {"score": "7.50", "feedback": "Good"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.score, Decimal("7.50"))
        self.assertEqual(self.submission.feedback, "Good")
        self.assertEqual(self.submission.status, "GRADED")
        self.assertEqual(self.submission.graded_by_id, self.admin.id)
        self.assertIsNotNone(self.submission.graded_at)

    # H-3d: progress records derive learner and reject cross-school IDs.
    def test_progress_create_derives_learner_and_server_fields(self):
        LessonProgress.objects.create(
            institution=self.school, learner=self.peer_learner, lesson=self.lesson,
        )
        self.client.force_authenticate(user=self.learner.user)
        response = self.client.post(reverse("lessonprogress-list"), {
            "lesson": self.lesson.id,
            "institution": self.other.id,
            "status": "COMPLETED",
            "completed_at": "2020-01-01T00:00:00Z",
            "synced_at": "2020-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        progress = LessonProgress.objects.get(learner=self.learner, lesson=self.lesson)
        self.assertEqual(progress.institution_id, self.school.id)
        self.assertEqual(progress.status, "NOT_STARTED")
        self.assertIsNone(progress.completed_at)
        self.assertIsNone(progress.synced_at)

        listing = self.client.get(reverse("lessonprogress-list"))
        self.assertEqual([row["id"] for row in self._results(listing)], [progress.id])

    def test_progress_writes_reject_foreign_lesson_or_learner(self):
        self.client.force_authenticate(user=self.admin)
        for payload in (
            {"lesson": self.foreign_lesson.id, "learner": self.learner.id},
            {"lesson": self.lesson.id, "learner": self.foreign_learner.id},
        ):
            response = self.client.post(reverse("lessonprogress-list"), payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        self.client.force_authenticate(user=self.learner.user)
        response = self.client.post(reverse("lessonprogress-list"), {
            "lesson": self.lesson.id, "learner": self.peer_learner.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_mark_complete_derives_learner_and_rejects_forged_ids(self):
        self.client.force_authenticate(user=self.learner.user)
        url = "/api/courses/progress/mark-complete/"
        for _ in range(2):
            response = self.client.post(url, {"lesson": self.lesson.id}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        progress = LessonProgress.objects.get(learner=self.learner, lesson=self.lesson)
        self.assertEqual(progress.institution_id, self.school.id)
        self.assertEqual(progress.status, "COMPLETED")
        self.assertEqual(
            LessonProgress.objects.filter(learner=self.learner, lesson=self.lesson).count(), 1,
        )

        for payload in (
            {"lesson": self.foreign_lesson.id},
            {"lesson": self.lesson.id, "learner": self.foreign_learner.id},
            {"lesson": self.lesson.id, "learner": self.peer_learner.id},
        ):
            response = self.client.post(url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_staff_mark_complete_still_validates_institution(self):
        self.client.force_authenticate(user=self.admin)
        url = "/api/courses/progress/mark-complete/"
        for payload in (
            {"lesson": self.foreign_lesson.id, "learner": self.learner.id},
            {"lesson": self.lesson.id, "learner": self.foreign_learner.id},
        ):
            response = self.client.post(url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        response = self.client.post(url, {
            "lesson": self.lesson.id, "learner": self.peer_learner.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
