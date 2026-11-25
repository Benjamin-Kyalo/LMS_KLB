"""School-admin profile edits cannot change institution identity or settings."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


class InstitutionProfileAllowlistTests(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="Allowlist Primary", code="ALP")
        self.other_kind = InstitutionType.objects.create(name="Allowlist Secondary", code="ALS")
        self.school = Institution.objects.create(
            name="Allowlist School", code="ALLOW", institution_type=self.kind,
            phone="0200000000", settings={"theme": "old"},
        )
        self.admin = User.objects.create_user(
            username="allowlist_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school,
        )
        self.platform = User.objects.create_user(
            username="allowlist_platform", password="StrongPass123!",
            role=Roles.SUPER_ADMIN, institution=self.school,
        )
        self.url = reverse("institution-mine")

    def test_profile_fields_still_update(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {
            "name": "Renamed School", "email": "office@example.org",
            "address_line": "1 Main Street", "town": "Nairobi",
            "county": "Nairobi", "postal_code": "00100",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, "Renamed School")
        self.assertEqual(self.school.email, "office@example.org")
        self.assertEqual(self.school.address_line, "1 Main Street")
        self.assertEqual(self.school.postal_code, "00100")

    def test_school_admin_cannot_change_identity_or_platform_fields(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {
            "name": "Still Our School",
            "code": "HACKED",
            "institution_type": self.other_kind.id,
            "is_active": False,
            "settings": {"theme": "attacker"},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, "Still Our School")
        self.assertEqual(self.school.code, "ALLOW")
        self.assertEqual(self.school.institution_type, self.kind)
        self.assertTrue(self.school.is_active)
        self.assertEqual(self.school.settings, {"theme": "old"})

    def test_platform_admin_keeps_full_update(self):
        self.client.force_authenticate(self.platform)
        response = self.client.patch(
            reverse("institution-detail", args=[self.school.id]),
            {"is_active": False, "settings": {"theme": "new"}}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school.refresh_from_db()
        self.assertFalse(self.school.is_active)
        self.assertEqual(self.school.settings, {"theme": "new"})

        # A platform admin can still use the mine shortcut with full fields.
        response = self.client.patch(self.url, {"code": "PLATFORM"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school.refresh_from_db()
        self.assertEqual(self.school.code, "PLATFORM")

    def test_profile_response_does_not_expose_settings(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {"motto": "Learn"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertNotIn("settings", response.data)
        self.assertIn("motto", response.data)
