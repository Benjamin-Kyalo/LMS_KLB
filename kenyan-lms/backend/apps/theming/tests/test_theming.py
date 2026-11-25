"""Theme palette catalogue, permissions and activation rules."""
from copy import deepcopy
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.constants import Roles
from apps.core.models import AuditLog
from apps.theming.catalogue import (
    DEFAULT_ACTIVE_SLUG, OCEAN_BLUE, PLUM_HARVEST, SWATCH_PALETTES,
)
from apps.theming.models import SiteContent, ThemePalette
from apps.theming.serializers import ThemePaletteSerializer
from apps.theming.site_content import DEFAULT_SITE_CONTENT, PUBLIC_SITE_KEY

User = get_user_model()


def palette_payload(name="Additional palette"):
    return {
        "name": name,
        "description": "A palette added through the admin API.",
        "source_label": "Administrator entry",
        **{f"shade_{step}": colour for step, colour in OCEAN_BLUE["shades"].items()},
    }


class ThemeManagementTests(APITestCase):
    def setUp(self):
        self.platform = User.objects.create_user(
            username="platform_admin", role=Roles.SUPER_ADMIN
        )
        self.school_admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN
        )
        self.learner = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER
        )
        self.client = APIClient()

    def test_initial_catalogue_and_public_active_endpoint(self):
        self.assertEqual(ThemePalette.objects.count(), 3 + len(SWATCH_PALETTES))
        self.assertEqual(ThemePalette.objects.filter(is_active=True).count(), 1)

        response = self.client.get(reverse("theme-active"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["slug"], PLUM_HARVEST["slug"])
        self.assertEqual(response.data["shades"][800], "#291720")
        self.assertTrue(response.data["is_builtin"])

    def test_plum_harvest_is_builtin_valid_and_default_active(self):
        self.assertEqual(DEFAULT_ACTIVE_SLUG, PLUM_HARVEST["slug"])
        record = ThemePalette.objects.get(slug=PLUM_HARVEST["slug"])
        self.assertTrue(record.is_builtin)
        self.assertTrue(record.is_active)
        self.assertEqual(record.source_label, PLUM_HARVEST["source_label"])
        for step, colour in PLUM_HARVEST["shades"].items():
            self.assertEqual(record.shades[step], colour)

        payload = {
            "name": record.name,
            "description": record.description,
            "source_label": record.source_label,
            **{f"shade_{step}": colour for step, colour in PLUM_HARVEST["shades"].items()},
        }
        serializer = ThemePaletteSerializer(instance=record, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_supplied_swatch_palettes_are_builtin_and_valid(self):
        for palette in SWATCH_PALETTES:
            with self.subTest(palette=palette["slug"]):
                record = ThemePalette.objects.get(slug=palette["slug"])
                self.assertTrue(record.is_builtin)
                self.assertFalse(record.is_active)
                self.assertEqual(record.source_label, palette["source_label"])
                for step, colour in palette["shades"].items():
                    self.assertEqual(record.shades[step], colour)

                payload = {
                    "name": record.name,
                    "description": record.description,
                    "source_label": record.source_label,
                    **{
                        f"shade_{step}": colour
                        for step, colour in palette["shades"].items()
                    },
                }
                serializer = ThemePaletteSerializer(instance=record, data=payload)
                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_platform_and_school_admins_can_change_the_catalogue(self):
        url = reverse("theme-palette-list")
        self.assertEqual(
            self.client.post(url, palette_payload("Unauthenticated"), format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.client.force_authenticate(user=self.learner)
        self.assertEqual(
            self.client.post(url, palette_payload("Learner attempt"), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(user=self.school_admin)
        school_response = self.client.post(url, palette_payload("School admin palette"), format="json")
        self.assertEqual(school_response.status_code, status.HTTP_201_CREATED, school_response.data)
        school_palette = ThemePalette.objects.get(pk=school_response.data["id"])
        self.assertEqual(school_palette.created_by, self.school_admin)
        self.assertFalse(school_palette.is_active)

        self.client.force_authenticate(user=self.platform)
        response = self.client.post(url, palette_payload("Custom ramp"), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = ThemePalette.objects.get(pk=response.data["id"])
        self.assertEqual(created.created_by, self.platform)
        self.assertFalse(created.is_active)

    def test_palette_validation_checks_hex_format_and_text_contrast(self):
        self.client.force_authenticate(user=self.platform)
        url = reverse("theme-palette-list")

        bad_hex = palette_payload("Bad hex")
        bad_hex["shade_500"] = "#00FF"
        response = self.client.post(url, bad_hex, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("shade_500", response.data)

        low_contrast = palette_payload("Low contrast")
        low_contrast["shade_700"] = "#FFFFFF"
        response = self.client.post(url, low_contrast, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("shade_700", response.data)

    def test_activation_switches_the_single_active_palette(self):
        sage = ThemePalette.objects.get(slug="sage-green")
        self.client.force_authenticate(user=self.platform)

        response = self.client.post(
            reverse("theme-palette-activate", args=[sage.pk]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["is_active"])
        self.assertEqual(ThemePalette.objects.filter(is_active=True).count(), 1)

        self.client.logout()
        active = self.client.get(reverse("theme-active"))
        self.assertEqual(active.data["slug"], "sage-green")
        self.assertEqual(active.data["shades"][100], "#F6FFF8")

    def test_builtin_and_active_palettes_cannot_be_deleted(self):
        self.client.force_authenticate(user=self.platform)
        builtin = ThemePalette.objects.get(slug="ocean-blue-serenity")

        forbidden = self.client.delete(
            reverse("theme-palette-detail", args=[builtin.pk]), format="json"
        )
        self.assertEqual(forbidden.status_code, status.HTTP_400_BAD_REQUEST, forbidden.data)

        created = self.client.post(
            reverse("theme-palette-list"), palette_payload("Temporary palette"), format="json"
        )
        palette_id = created.data["id"]
        self.client.post(
            reverse("theme-palette-activate", args=[palette_id]), {}, format="json"
        )
        forbidden = self.client.delete(
            reverse("theme-palette-detail", args=[palette_id]), format="json"
        )
        self.assertEqual(forbidden.status_code, status.HTTP_400_BAD_REQUEST, forbidden.data)

    def test_public_site_content_defaults_and_admin_edits(self):
        url = reverse("site-content")
        first = self.client.get(url)
        self.assertEqual(first.status_code, status.HTTP_200_OK, first.data)
        self.assertEqual(first.data["roles"]["title"], "Where do you fit?")
        self.assertEqual(first.data["header"]["brand"]["mark"], "KLB")
        self.assertEqual(first.data["library"]["booksTitle"], "Books to explore")
        self.assertEqual(first.data["hero"]["imageSrc"], "/images/hero-community.png")
        self.assertNotIn("facts", first.data)
        self.assertEqual(
            [card["key"] for card in first.data["roles"]["cards"]],
            ["learners", "guardians", "teachers"],
        )

        self.client.force_authenticate(user=self.learner)
        denied = self.client.patch(url, {"content": {}}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["footer"]["name"] = "Our school learning site"
        content["roles"]["title"] = "Find your place here"
        self.client.force_authenticate(user=self.platform)
        saved = self.client.patch(url, {"content": content}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self.assertEqual(saved.data["footer"]["name"], "Our school learning site")

        self.client.force_authenticate(user=self.school_admin)
        styled = self.client.patch(
            url,
            {"content": {"styles": {"hero": {"background": "#123456", "text": "#FFFFFF"}}}},
            format="json",
        )
        self.assertEqual(styled.status_code, status.HTTP_200_OK, styled.data)
        self.assertEqual(styled.data["styles"]["hero"]["background"], "#123456")
        self.assertEqual(styled.data["footer"]["name"], "Our school learning site")

        self.client.logout()
        public = self.client.get(url)
        self.assertEqual(public.data["footer"]["name"], "Our school learning site")
        self.assertEqual(public.data["roles"]["title"], "Find your place here")
        self.assertEqual(public.data["styles"]["hero"]["text"], "#FFFFFF")
        self.assertEqual(SiteContent.objects.count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="site_content.updated").exists())

    def test_section_styles_are_allowlisted_and_legible(self):
        url = reverse("site-content")
        self.client.force_authenticate(user=self.platform)

        injected = self.client.patch(
            url,
            {"content": {"styles": {"hero": {"background": "url(javascript:alert(1))"}}}},
            format="json",
        )
        self.assertEqual(injected.status_code, status.HTTP_400_BAD_REQUEST, injected.data)
        self.assertIn("styles.hero.background", str(injected.data))

        unsafe = self.client.patch(
            url,
            {"content": {"styles": {"hero": {"background": "#FFFFFF", "text": "#FFFFFF"}}}},
            format="json",
        )
        self.assertEqual(unsafe.status_code, status.HTTP_400_BAD_REQUEST, unsafe.data)
        self.assertIn("4.5:1", str(unsafe.data))

        saved = self.client.patch(
            url,
            {
                "content": {
                    "styles": {
                        "tutor": {
                            "background": "#102A43",
                            "text": "#FFFFFF",
                            "accent": "#FFB067",
                            "radius": "8px",
                            "spacing": "compact",
                            "customCss": "body{display:none}",
                        },
                    },
                },
            },
            format="json",
        )
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        tutor = saved.data["styles"]["tutor"]
        self.assertEqual(tutor["background"], "#102A43")
        self.assertEqual(tutor["radius"], "8px")
        self.assertEqual(tutor["spacing"], "compact")
        self.assertNotIn("customCss", tutor)

        self.client.logout()
        public = self.client.get(url)
        self.assertEqual(public.data["styles"]["tutor"]["accent"], "#FFB067")
        self.assertNotIn("customCss", str(public.data["styles"]))

    def test_retired_content_manager_preview_never_returns(self):
        url = reverse("site-content")
        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["roles"]["cards"] = list(content["roles"]["cards"]) + [{
            "key": "content",
            "label": "Content managers",
            "title": "Curate learning resources",
            "copy": "Retired preview.",
            "to": "/login?role=CONTENT_MANAGER",
            "action": "Content manager workspace",
            "rights": [],
            "content": [],
        }]

        self.client.force_authenticate(user=self.platform)
        saved = self.client.patch(url, {"content": content}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        saved_keys = [card["key"] for card in saved.data["roles"]["cards"]]
        self.assertNotIn("content", saved_keys)

        self.client.logout()
        public = self.client.get(url)
        self.assertEqual(
            [card["key"] for card in public.data["roles"]["cards"]],
            ["learners", "guardians", "teachers"],
        )
        self.assertNotIn("Content managers", str(public.data["roles"]["cards"]))

    def test_retired_offline_queue_nav_item_never_returns(self):
        url = reverse("site-content")
        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["app"]["portalNav"] = list(content["app"]["portalNav"]) + [
            {"key": "sync", "label": "Offline queue"},
        ]

        self.client.force_authenticate(user=self.platform)
        saved = self.client.patch(url, {"content": content}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self.assertNotIn("sync", [item["key"] for item in saved.data["app"]["portalNav"]])

        self.client.logout()
        public = self.client.get(url)
        self.assertNotIn("sync", [item["key"] for item in public.data["app"]["portalNav"]])
        self.assertNotIn("Offline queue", str(public.data["app"]["portalNav"]))

    def test_default_public_copy_does_not_promise_offline_behaviour(self):
        copy = str(DEFAULT_SITE_CONTENT).lower()
        for phrase in (
            "offline",
            "sync on reconnect",
            "queued until reconnected",
            "continue offline",
        ):
            self.assertNotIn(phrase, copy)

    def test_retired_quick_facts_never_return(self):
        url = reverse("site-content")
        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["facts"] = [
            {"value": "14", "label": "connected application modules"},
            {"value": "Offline", "label": "changes queued until reconnected"},
        ]

        self.client.force_authenticate(user=self.platform)
        saved = self.client.patch(url, {"content": content}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self.assertNotIn("facts", saved.data)

        self.client.logout()
        public = self.client.get(url)
        self.assertNotIn("facts", public.data)
        self.assertNotIn("connected application modules", str(public.data))

    def test_platform_admin_can_upload_and_publish_homepage_photo(self):
        buffer = BytesIO()
        Image.new("RGB", (800, 450), color="blue").save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "hero.png", buffer.getvalue(), content_type="image/png",
        )
        url = reverse("site-hero-image")
        self.client.force_authenticate(user=self.platform)

        response = self.client.post(url, {"image": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        image_src = response.data["imageSrc"]
        stored_path = image_src.replace("/media/", "", 1)
        self.assertTrue(stored_path.startswith("site-content/hero/hero-"))
        self.assertTrue(default_storage.exists(stored_path))
        self.assertEqual(response.data["content"]["hero"]["imageSrc"], image_src)

        record = SiteContent.objects.get(key=PUBLIC_SITE_KEY)
        self.assertEqual(record.content["hero"]["imageSrc"], image_src)
        self.assertEqual(record.updated_by, self.platform)
        self.assertTrue(AuditLog.objects.filter(
            action="site_content.hero_image_uploaded",
        ).exists())
        default_storage.delete(stored_path)

    def test_platform_admin_can_upload_any_managed_photo_slot(self):
        buffer = BytesIO()
        Image.new("RGB", (800, 450), color="purple").save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "progress.png", buffer.getvalue(), content_type="image/png",
        )
        url = reverse("site-image")
        self.client.force_authenticate(user=self.platform)

        response = self.client.post(
            url, {"slot": "insights", "image": upload}, format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        image_src = response.data["imageSrc"]
        stored_path = image_src.replace("/media/", "", 1)
        self.assertTrue(stored_path.startswith("site-content/insights/insights-"))
        self.assertTrue(default_storage.exists(stored_path))
        self.assertEqual(response.data["content"]["insights"]["imageSrc"], image_src)

        record = SiteContent.objects.get(key=PUBLIC_SITE_KEY)
        self.assertEqual(record.content["insights"]["imageSrc"], image_src)
        self.assertEqual(record.updated_by, self.platform)
        audit = AuditLog.objects.get(action="site_content.image_uploaded")
        self.assertEqual(audit.details["slot"], "insights")
        self.assertEqual(audit.details["path"], stored_path)
        default_storage.delete(stored_path)

    def test_platform_admin_can_remove_and_reset_a_managed_photo(self):
        slot_url = reverse("site-image-slot", args=["workspace-learning"])
        reset_url = reverse("site-image-reset", args=["workspace-learning"])
        self.client.force_authenticate(user=self.platform)

        removed = self.client.delete(slot_url)
        self.assertEqual(removed.status_code, status.HTTP_200_OK, removed.data)
        self.assertEqual(removed.data["imageSrc"], "")
        self.assertEqual(removed.data["content"]["workspaces"]["cards"][0]["image"], "")
        self.assertTrue(AuditLog.objects.filter(
            action="site_content.image_removed", details__slot="workspace-learning",
        ).exists())

        restored = self.client.post(reset_url, {})
        self.assertEqual(restored.status_code, status.HTTP_200_OK, restored.data)
        self.assertEqual(
            restored.data["imageSrc"],
            DEFAULT_SITE_CONTENT["workspaces"]["cards"][0]["image"],
        )
        self.assertTrue(AuditLog.objects.filter(
            action="site_content.image_reset", details__slot="workspace-learning",
        ).exists())

    def test_photo_upload_rejects_unknown_slots(self):
        buffer = BytesIO()
        Image.new("RGB", (800, 450), color="orange").save(buffer, format="PNG")
        upload = SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")
        self.client.force_authenticate(user=self.platform)

        response = self.client.post(
            reverse("site-image"),
            {"slot": "hero.title", "image": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slot", str(response.data).lower())
        self.assertFalse(default_storage.exists("site-content/hero.title"))

    def test_photo_upload_rejects_non_images_and_non_admins(self):
        url = reverse("site-hero-image")
        text_file = SimpleUploadedFile(
            "hero.txt", b"not an image", content_type="text/plain",
        )
        self.client.force_authenticate(user=self.platform)
        response = self.client.post(url, {"image": text_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", str(response.data).lower())

        self.client.force_authenticate(user=self.learner)
        buffer = BytesIO()
        Image.new("RGB", (800, 450), color="green").save(buffer, format="PNG")
        png = SimpleUploadedFile("hero.png", buffer.getvalue(), content_type="image/png")
        forbidden = self.client.post(url, {"image": png}, format="multipart")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_admin_can_upload_remove_and_reset_managed_photos(self):
        buffer = BytesIO()
        Image.new("RGB", (800, 450), color="green").save(buffer, format="PNG")
        upload = SimpleUploadedFile(
            "insights.png", buffer.getvalue(), content_type="image/png",
        )
        self.client.force_authenticate(user=self.school_admin)

        published = self.client.post(
            reverse("site-image"),
            {"slot": "insights", "image": upload},
            format="multipart",
        )
        self.assertEqual(published.status_code, status.HTTP_201_CREATED, published.data)
        image_src = published.data["imageSrc"]
        stored_path = image_src.replace("/media/", "", 1)
        self.assertTrue(stored_path.startswith("site-content/insights/insights-"))
        self.assertTrue(default_storage.exists(stored_path))
        record = SiteContent.objects.get(key=PUBLIC_SITE_KEY)
        self.assertEqual(record.content["insights"]["imageSrc"], image_src)
        self.assertEqual(record.updated_by, self.school_admin)

        removed = self.client.delete(reverse("site-image-slot", args=["insights"]))
        self.assertEqual(removed.status_code, status.HTTP_200_OK, removed.data)
        self.assertEqual(removed.data["imageSrc"], "")

        restored = self.client.post(reverse("site-image-reset", args=["insights"]), {})
        self.assertEqual(restored.status_code, status.HTTP_200_OK, restored.data)
        self.assertEqual(
            restored.data["imageSrc"],
            DEFAULT_SITE_CONTENT["insights"]["imageSrc"],
        )
        self.assertTrue(AuditLog.objects.filter(
            action="site_content.image_uploaded", user=self.school_admin,
        ).exists())
        default_storage.delete(stored_path)

    def test_saved_offline_copy_is_sanitised(self):
        url = reverse("site-content")
        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["hero"]["description"] = (
            "A single KLB ecosystem for lessons, school records and digital "
            "textbooks. It is built for competency based learning and works "
            "when the network is not."
        )
        content["workspaces"]["cards"][0]["title"] = "Lessons that continue offline"
        content["roles"]["cards"][0]["copy"] = (
            "Open your courses, assignments, quizzes and digital books. Your "
            "work waits safely on the device and syncs when you are back online."
        )
        content["roles"]["cards"][0]["rights"][2] = (
            "Submit work while offline and sync on reconnect"
        )
        content["app"]["portalNav"].append({"key": "sync", "label": "Offline queue"})

        self.client.force_authenticate(user=self.platform)
        saved = self.client.patch(url, {"content": content}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        self.assertNotIn("offline", str(saved.data).lower())

        self.client.logout()
        public = self.client.get(url)
        self.assertNotIn("offline", str(public.data).lower())
        self.assertEqual(
            public.data["workspaces"]["cards"][0]["title"],
            "Learning in one place",
        )

    def test_site_content_rejects_unsafe_links(self):
        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["header"]["signInHref"] = "javascript:alert(1)"
        self.client.force_authenticate(user=self.platform)
        response = self.client.patch(
            reverse("site-content"), {"content": content}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("header.signInHref", response.data["content"])

        content = deepcopy(DEFAULT_SITE_CONTENT)
        content["hero"]["imageSrc"] = "javascript:alert(1)"
        response = self.client.patch(
            reverse("site-content"), {"content": content}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("hero.imageSrc", response.data["content"])
