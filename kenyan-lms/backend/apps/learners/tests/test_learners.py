"""Learner creation, isolation and validation tests."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


def rows(response):
    """List endpoints are paginated: return just the result rows."""
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class LearnerTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(name="Test School", code="T001", institution_type=kind)
        self.other = Institution.objects.create(name="Other School", code="O001", institution_type=kind)
        self.admin = User.objects.create_user(
            username="admin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )

    def test_create_learner_creates_user_and_profile(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("learner-list"), {
            "username": "learner1", "first_name": "Amina", "last_name": "Otieno",
            "admission_number": "ADM001",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Learner.objects.count(), 1)
        learner = Learner.objects.first()
        self.assertEqual(learner.user.role, Roles.LEARNER)
        self.assertFalse(learner.user.has_usable_password())
        self.assertFalse(learner.user.must_change_password)
        self.assertEqual(learner.institution, self.school)

    def test_learner_cannot_be_seen_from_another_school(self):
        other_user = User.objects.create_user(
            username="other", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.other,
        )
        Learner.objects.create(user=other_user, institution=self.other, admission_number="ADM999")
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("learner-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(rows(response)), 0)

    def test_duplicate_admission_number_rejected(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "username": "l1", "first_name": "A", "last_name": "B",
            "admission_number": "ADM001",
        }
        self.client.post(reverse("learner-list"), payload)
        payload["username"] = "l2"
        response = self.client.post(reverse("learner-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
