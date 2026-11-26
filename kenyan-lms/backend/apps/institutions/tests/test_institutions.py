"""Institution isolation and access tests."""
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass

User = get_user_model()


def rows(response):
    """List endpoints are paginated: return just the result rows."""
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class InstitutionIsolationTests(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="Secondary", code="SEC")
        self.school_a = Institution.objects.create(name="School A", code="A001", institution_type=self.kind)
        self.school_b = Institution.objects.create(name="School B", code="B001", institution_type=self.kind)
        self.admin_a = User.objects.create_user(
            username="admina", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school_a,
        )

    def test_admin_sees_only_own_institution(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(reverse("institution-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = rows(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["code"], "A001")

    def test_platform_admin_sees_all_institutions(self):
        root = User.objects.create_user(username="root", password="StrongPass123!", role=Roles.SUPER_ADMIN)
        self.client.force_authenticate(user=root)
        response = self.client.get(reverse("institution-list"))
        self.assertEqual(len(rows(response)), 2)

    def test_school_admin_cannot_create_institution(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(reverse("institution-list"), {
            "name": "School C", "code": "C001", "institution_type": self.kind.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_admin_can_update_own_profile(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.patch(reverse("institution-mine"), {
            "phone": "0201234567",
            "motto": "Learn with purpose",
            "website": "https://school.example",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school_a.refresh_from_db()
        self.assertEqual(self.school_a.phone, "0201234567")
        self.assertEqual(self.school_a.motto, "Learn with purpose")

    def test_logo_upload_accepts_image_and_rejects_text_file(self):
        self.client.force_authenticate(user=self.admin_a)
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="green").save(buffer, format="PNG")
        png = SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")
        response = self.client.patch(reverse("institution-mine"), {"logo": png}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.school_a.refresh_from_db()
        self.assertTrue(self.school_a.logo.name.startswith("institutions/logos/"))
        self.school_a.logo.delete(save=False)

        text_file = SimpleUploadedFile("logo.txt", b"not an image", content_type="text/plain")
        response = self.client.patch(reverse("institution-mine"), {"logo": text_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", str(response.data).lower())

    def test_learner_cannot_edit_school_profile(self):
        learner = User.objects.create_user(
            username="learner1", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school_a,
        )
        self.client.force_authenticate(user=learner)
        response = self.client.patch(reverse("institution-mine"), {
            "phone": "0700000000",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.school_a.refresh_from_db()
        self.assertNotEqual(self.school_a.phone, "0700000000")


class SchoolClassDisplayTests(APITestCase):
    def test_display_name_includes_stream(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        school = Institution.objects.create(name="Display School", code="DSP", institution_type=kind)
        year = AcademicYear.objects.create(
            institution=school, name="2026",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        klass = SchoolClass.objects.create(
            institution=school, academic_year=year, name="Grade 4", stream="A"
        )
        self.assertEqual(klass.display_name, "Grade 4 A")

        admin = User.objects.create_user(
            username="classadmin", password="StrongPass123!",
            role=Roles.ADMIN, institution=school,
        )
        self.client.force_authenticate(user=admin)
        response = self.client.get(reverse("schoolclass-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(rows(response)[0]["display_name"], "Grade 4 A")
