"""Low-bandwidth client configuration and narrow conflict checks."""
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.theming.models import SiteContent, ThemePalette
from apps.theming.site_content import PUBLIC_SITE_KEY

User = get_user_model()


class ClientConfigTests(APITestCase):
    def test_config_is_public_and_contains_no_secrets(self):
        response = self.client.get(reverse("core-client-config"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["offline"]["enabled"])
        self.assertEqual(response["Cache-Control"], "public, max-age=300")

        blob = str(response.data).lower()
        for forbidden in ("password", "secret", "csrf", "cookie", "bearer", "token"):
            self.assertNotIn(forbidden, blob)

    @override_settings(
        OFFLINE_MODE_ENABLED=True,
        OFFLINE_CACHE_PATHS=["/api/theming/site-content/"],
        OFFLINE_OUTBOX_PATHS=["/api/theming/site-content/"],
    )
    def test_operator_switches_are_exposed_without_service_worker(self):
        response = self.client.get(reverse("core-client-config"))
        self.assertTrue(response.data["offline"]["enabled"])
        self.assertTrue(response.data["offline"]["read_cache"]["enabled"])
        self.assertTrue(response.data["offline"]["outbox"]["enabled"])
        self.assertEqual(
            response.data["offline"]["read_cache"]["paths"],
            ["/api/theming/site-content/"],
        )
        self.assertFalse(response.data["offline"]["service_worker"])
        self.assertFalse(response.data["offline"]["native_app"])


class ThemeConflictTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Offline Primary", code="OFP")
        school = Institution.objects.create(
            name="Offline School", code="OFF", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN, institution=school
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_site_content_patch_rejects_stale_if_match(self):
        record, _ = SiteContent.objects.get_or_create(key=PUBLIC_SITE_KEY)
        url = reverse("site-content")
        response = self.client.patch(
            url, {"content": {}}, format="json",
            HTTP_IF_MATCH="2000-01-01T00:00:00+00:00",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.data)
        self.assertEqual(response.data["code"], "conflict")
        self.assertEqual(response.data["server"]["id"], record.pk)
        self.assertEqual(response.data["server"]["updated_at"], record.updated_at.isoformat())

        fresh = self.client.patch(
            url, {"content": {}}, format="json",
            HTTP_IF_MATCH=record.updated_at.isoformat(),
        )
        self.assertEqual(fresh.status_code, status.HTTP_200_OK, fresh.data)

    def test_palette_patch_rejects_stale_if_match(self):
        colour = "#023E8A"
        palette = ThemePalette.objects.create(
            name="Offline palette",
            shade_900=colour, shade_800=colour, shade_700=colour,
            shade_600=colour, shade_500=colour, shade_400=colour,
            shade_300=colour, shade_200=colour, shade_100=colour,
        )
        url = reverse("theme-palette-detail", args=[palette.pk])
        response = self.client.patch(
            url, {"name": "Renamed"}, format="json",
            HTTP_IF_MATCH="2000-01-01T00:00:00+00:00",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.data)
        self.assertEqual(response.data["code"], "conflict")
        self.assertIn("updated_at", response.data["server"])

        fresh = self.client.patch(
            url, {"name": "Renamed"}, format="json",
            HTTP_IF_MATCH=palette.updated_at.isoformat(),
        )
        self.assertEqual(fresh.status_code, status.HTTP_200_OK, fresh.data)
