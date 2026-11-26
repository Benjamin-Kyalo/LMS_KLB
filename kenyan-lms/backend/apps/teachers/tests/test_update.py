"""Teacher profile edit tests."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.teachers.models import Teacher

User = get_user_model()


class TeacherUpdateTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        school = Institution.objects.create(name="Test School", code="T001", institution_type=kind)
        self.admin = User.objects.create_user(
            username="admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=school,
        )
        self.teacher_user = User.objects.create_user(
            username="teacher1", first_name="Mary", last_name="Wekesa",
            password="StrongPass123!", role=Roles.TEACHER, institution=school,
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, institution=school, staff_number="T001",
        )

    def test_patch_updates_teacher_and_nested_user_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(reverse("teacher-detail", args=[self.teacher.pk]), {
            "username": "teacher1", "first_name": "Mary", "last_name": "Wekesa",
            "email": "mary@example.com", "phone": "", "staff_number": "T001",
            "subjects": [],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher_user.refresh_from_db()
        self.assertEqual(self.teacher_user.email, "mary@example.com")
