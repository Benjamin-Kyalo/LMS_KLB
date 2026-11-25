"""Focused ownership and grade-integrity tests for exercise attempts."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.content.models import (
    Chapter, DigitalTextbook, Exercise, ExerciseAttempt, Publisher,
)
from apps.core.constants import ContentStatus, Roles
from apps.institutions.models import (
    AcademicYear, Institution, InstitutionType, SchoolClass, Subject,
)
from apps.learners.models import Learner

User = get_user_model()
PASSWORD = "StrongPass123!"


class ExerciseAttemptSecurityTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Exercise Type", code="EXT")
        self.school = Institution.objects.create(
            name="Exercise School", code="EXT-A", institution_type=kind,
        )
        self.other = Institution.objects.create(
            name="Other Exercise School", code="EXT-B", institution_type=kind,
        )
        year = AcademicYear.objects.create(
            institution=self.school, name="2026", start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        school_class = SchoolClass.objects.create(
            institution=self.school, academic_year=year, name="Grade 5",
        )
        subject = Subject.objects.create(institution=self.school, name="Mathematics")
        publisher = Publisher.objects.create(name="Exercise Publisher", code="EXPUB")
        textbook = DigitalTextbook.objects.create(
            publisher=publisher, title="Exercise textbook", subject=subject,
            status=ContentStatus.PUBLISHED, published_at=timezone.now(),
        )
        chapter = Chapter.objects.create(textbook=textbook, title="Chapter 1")
        second_chapter = Chapter.objects.create(
            textbook=textbook, title="Chapter 2", chapter_number=2,
        )
        self.exercise = Exercise.objects.create(
            chapter=chapter, title="Exercise 1", max_score=Decimal("10"),
        )
        self.other_exercise = Exercise.objects.create(
            chapter=second_chapter, title="Exercise 2", max_score=Decimal("10"),
        )

        self.admin = User.objects.create_user(
            username="exercise-admin", password=PASSWORD,
            role=Roles.ADMIN, institution=self.school,
        )
        self.foreign_admin = User.objects.create_user(
            username="exercise-admin-b", password=PASSWORD,
            role=Roles.ADMIN, institution=self.other,
        )

        learner_user = User.objects.create_user(
            username="exercise-learner", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school,
            admission_number="EXT-L1", class_room=school_class,
        )
        peer_user = User.objects.create_user(
            username="exercise-peer", password=PASSWORD,
            role=Roles.LEARNER, institution=self.school,
        )
        self.peer = Learner.objects.create(
            user=peer_user, institution=self.school,
            admission_number="EXT-L2", class_room=school_class,
        )

    @staticmethod
    def _results(response):
        return response.data["results"] if isinstance(response.data, dict) else response.data

    def test_learner_create_overrides_forged_ownership_and_grade_fields(self):
        self.client.force_authenticate(user=self.learner.user)
        response = self.client.post(reverse("exerciseattempt-list"), {
            "exercise": self.exercise.id,
            "learner": self.peer.id,
            "institution": self.other.id,
            "answers": [{"question": 1, "answer": "A"}],
            "score": "999",
            "completed_at": "2020-01-01T00:00:00Z",
            "synced_at": "2020-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        attempt = ExerciseAttempt.objects.get(pk=response.data["id"])
        self.assertEqual(attempt.learner_id, self.learner.id)
        self.assertEqual(attempt.institution_id, self.school.id)
        self.assertIsNone(attempt.score)
        self.assertIsNone(attempt.completed_at)
        self.assertIsNone(attempt.synced_at)

    def test_learner_reads_and_updates_only_their_own_attempts(self):
        own = ExerciseAttempt.objects.create(
            institution=self.school, exercise=self.exercise, learner=self.learner,
        )
        peer_attempt = ExerciseAttempt.objects.create(
            institution=self.school, exercise=self.exercise, learner=self.peer,
        )
        self.client.force_authenticate(user=self.learner.user)

        listing = self.client.get(reverse("exerciseattempt-list"))
        self.assertEqual([row["id"] for row in self._results(listing)], [own.id])

        peer_url = reverse("exerciseattempt-detail", args=[peer_attempt.id])
        self.assertEqual(
            self.client.patch(peer_url, {"answers": ["hacked"]}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )

        own_url = reverse("exerciseattempt-detail", args=[own.id])
        response = self.client.patch(own_url, {
            "answers": ["A"],
            "score": "999",
            "learner": self.peer.id,
            "institution": self.other.id,
            "exercise": self.other_exercise.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        own.refresh_from_db()
        self.assertEqual(own.answers, ["A"])
        self.assertIsNone(own.score)
        self.assertEqual(own.learner_id, self.learner.id)
        self.assertEqual(own.institution_id, self.school.id)
        self.assertEqual(own.exercise_id, self.exercise.id)
        peer_attempt.refresh_from_db()
        self.assertEqual(peer_attempt.answers, [])

    def test_staff_must_supply_a_learner_and_cannot_cross_institutions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("exerciseattempt-list"), {
            "exercise": self.exercise.id,
            "answers": ["A"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        foreign_learner_user = User.objects.create_user(
            username="exercise-foreign", password=PASSWORD,
            role=Roles.LEARNER, institution=self.other,
        )
        foreign_learner = Learner.objects.create(
            user=foreign_learner_user, institution=self.other,
            admission_number="EXT-B1",
        )
        response = self.client.post(reverse("exerciseattempt-list"), {
            "exercise": self.exercise.id,
            "learner": foreign_learner.id,
            "answers": ["A"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        response = self.client.post(reverse("exerciseattempt-list"), {
            "exercise": self.exercise.id,
            "learner": self.learner.id,
            "answers": ["A"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(
            ExerciseAttempt.objects.get(pk=response.data["id"]).institution_id,
            self.school.id,
        )

    def test_foreign_school_cannot_see_another_schools_attempts(self):
        attempt = ExerciseAttempt.objects.create(
            institution=self.school, exercise=self.exercise, learner=self.learner,
        )
        self.client.force_authenticate(user=self.foreign_admin)
        response = self.client.get(reverse("exerciseattempt-detail", args=[attempt.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
