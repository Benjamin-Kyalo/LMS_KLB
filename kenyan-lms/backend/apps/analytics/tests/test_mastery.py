"""Derived mastery badges: read-only displays over competency evidence."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.analytics.engine import build_mastery_badges
from apps.core.constants import MasteryLevel, Roles
from apps.curriculum.models import Competency, CompetencyEvidence, CurriculumFramework
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


class MasteryBadgeTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Mastery Primary", code="MBP")
        self.school = Institution.objects.create(
            name="Mastery School", code="MAST", institution_type=kind
        )
        self.other_school = Institution.objects.create(
            name="Other Mastery School", code="MOT", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN, institution=self.school
        )
        learner_user = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER, institution=self.school
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="MAS-001"
        )
        other_learner_user = User.objects.create_user(
            username="other_learner", role=Roles.LEARNER, institution=self.other_school
        )
        self.other_learner = Learner.objects.create(
            user=other_learner_user, institution=self.other_school,
            admission_number="MOT-001",
        )
        framework = CurriculumFramework.objects.create(name="CBC", code="CBC", version="1.0")
        self.competency = Competency.objects.create(
            framework=framework, name="Numeracy", code="NUM"
        )
        self.other_competency = Competency.objects.create(
            framework=framework, name="Literacy", code="LIT"
        )
        self.client = APIClient()

    def _evidence(self, school, learner, competency, level):
        return CompetencyEvidence.objects.create(
            institution=school, learner=learner, competency=competency,
            achieved_level=level,
        )

    def test_badges_are_derived_per_competency_and_write_nothing(self):
        self._evidence(self.school, self.learner, self.competency, MasteryLevel.EXTENDING)
        self._evidence(self.school, self.learner, self.competency, MasteryLevel.ACHIEVING)
        self._evidence(self.school, self.learner, self.competency, MasteryLevel.DEVELOPING)
        self._evidence(self.school, self.learner, self.other_competency, MasteryLevel.DEVELOPING)
        # Evidence without a competency is not a badge signal.
        self._evidence(self.school, self.learner, None, MasteryLevel.EXTENDING)
        before = CompetencyEvidence.objects.count()

        result = build_mastery_badges(self.school)

        self.assertEqual(CompetencyEvidence.objects.count(), before)
        self.assertEqual(result["summary"]["badges"], 2)
        self.assertEqual(result["summary"]["earned_badges"], 1)
        numeracy = next(
            row for row in result["badges"]
            if row["competency_id"] == self.competency.pk
        )
        self.assertEqual(numeracy["mastery_level"], MasteryLevel.ACHIEVING)
        self.assertTrue(numeracy["earned"])
        self.assertEqual(numeracy["evidence_count"], 3)
        self.assertEqual(numeracy["mastery_score"], 0.75)
        literacy = next(
            row for row in result["badges"]
            if row["competency_id"] == self.other_competency.pk
        )
        self.assertEqual(literacy["mastery_level"], MasteryLevel.DEVELOPING)
        self.assertFalse(literacy["earned"])
        self.assertIn("derived displays", result["rules"]["note"])

    def test_invalid_mastery_filter_is_rejected_by_engine_and_api(self):
        with self.assertRaises(ValueError):
            build_mastery_badges(self.school, {"mastery_level": "MASTER"})

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("analytics-mastery"), {"mastery_level": "MASTER"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mastery_level", response.data)

    def test_staff_report_is_scoped_and_read_only(self):
        self._evidence(self.school, self.learner, self.competency, MasteryLevel.EXTENDING)
        self._evidence(
            self.other_school, self.other_learner, self.competency, MasteryLevel.BEGINNING
        )
        url = reverse("analytics-mastery")

        self.client.force_authenticate(user=self.learner.user)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        guardian = User.objects.create_user(
            username="demo_guardian", role=Roles.GUARDIAN, institution=self.school
        )
        self.client.force_authenticate(user=guardian)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["summary"]["badges"], 1)
        self.assertEqual(response.data["badges"][0]["learner_id"], self.learner.pk)
        self.assertEqual(response.data["scope"]["institution_id"], self.school.pk)

        filtered = self.client.get(url, {"learner": self.other_learner.pk})
        self.assertEqual(filtered.data["summary"]["badges"], 0)

    def test_learner_only_receives_own_badges(self):
        self._evidence(self.school, self.learner, self.competency, MasteryLevel.EXTENDING)
        classmate_user = User.objects.create_user(
            username="classmate", role=Roles.LEARNER, institution=self.school
        )
        classmate = Learner.objects.create(
            user=classmate_user, institution=self.school, admission_number="MAS-002"
        )
        self._evidence(self.school, classmate, self.competency, MasteryLevel.ACHIEVING)

        self.client.force_authenticate(user=self.learner.user)
        response = self.client.get(reverse("analytics-my-mastery"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["summary"]["badges"], 1)
        self.assertEqual(response.data["badges"][0]["learner_id"], self.learner.pk)
        self.assertNotIn("notes", response.data["badges"][0])
