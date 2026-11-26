"""Server-side guardian search used by the link-guardian picker."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


def rows(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class GuardianSearchTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(
            name="Search School", code="SRCH", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="searchadmin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school,
        )
        self.guardian_user = User.objects.create_user(
            username="mary_wambui", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=self.school,
            first_name="Mary", last_name="Wambui",
        )
        self.guardian = Guardian.objects.create(
            user=self.guardian_user, institution=self.school,
            guardian_number="GD_SRCH_001", phone="0700000001",
        )
        self.client.force_authenticate(user=self.admin)

    def test_search_by_guardian_number(self):
        response = self.client.get(reverse("guardian-list"), {"search": "GD_SRCH_001"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in rows(response)], [self.guardian.id])

    def test_search_by_username_and_phone(self):
        for needle in ("mary_wambui", "0700000001"):
            response = self.client.get(reverse("guardian-list"), {"search": needle})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(rows(response)), 1)
