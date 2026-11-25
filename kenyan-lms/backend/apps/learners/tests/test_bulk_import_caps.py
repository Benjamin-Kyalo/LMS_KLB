"""Bounded CSV bulk import tests."""
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()
HEADER = "username,first_name,last_name,admission_number\n"


def csv_text(row_count, start=0):
    return HEADER + "".join(
        f"bulk{start + i},First,Last,ADM{start + i}\n" for i in range(row_count)
    )


class BulkImportCapTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Import Primary", code="IMP")
        school = Institution.objects.create(
            name="Import School", code="IMPS", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="import_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=school,
        )
        self.client.force_authenticate(self.admin)
        self.url = reverse("learner-bulk-import")

    def test_valid_import_still_works(self):
        response = self.client.post(self.url, {"csv_text": csv_text(2)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["imported"], 2)
        self.assertEqual(Learner.objects.count(), 2)

    @override_settings(LEARNER_CSV_MAX_ROWS=2)
    def test_row_cap_rejects_extra_rows_without_importing(self):
        response = self.client.post(self.url, {"csv_text": csv_text(3)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too many rows", str(response.data).lower())
        self.assertFalse(Learner.objects.exists())

    @override_settings(LEARNER_CSV_MAX_ROWS=2)
    def test_row_cap_allows_exactly_the_limit(self):
        response = self.client.post(self.url, {"csv_text": csv_text(2)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Learner.objects.count(), 2)

    @override_settings(LEARNER_CSV_MAX_BYTES=50)
    def test_byte_cap_rejects_oversized_text(self):
        response = self.client.post(self.url, {"csv_text": csv_text(1)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too large", str(response.data).lower())
        self.assertFalse(Learner.objects.exists())

    def test_default_caps_are_bounded(self):
        oversized = csv_text(1) + "x" * (1024 * 1024)
        response = self.client.post(self.url, {"csv_text": oversized}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too large", str(response.data).lower())

        too_many_rows = csv_text(501)
        response = self.client.post(self.url, {"csv_text": too_many_rows}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too many rows", str(response.data).lower())
        self.assertFalse(Learner.objects.exists())
