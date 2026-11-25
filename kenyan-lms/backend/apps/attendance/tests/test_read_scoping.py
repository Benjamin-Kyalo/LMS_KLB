"""Attendance read scoping for staff, learners and guardians."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.attendance.models import AttendanceRecord
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


def rows(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class AttendanceReadScopingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        kind = InstitutionType.objects.create(name="Attendance Scope", code="ATS")
        cls.school = Institution.objects.create(
            name="Attendance School", code="ATSCOPE", institution_type=kind
        )
        cls.other_school = Institution.objects.create(
            name="Attendance Other", code="ATSCOPE2", institution_type=kind
        )
        cls.admin = User.objects.create_user(
            username="attscope_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=cls.school,
        )
        cls.learner_user = User.objects.create_user(
            username="attscope_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.learner = Learner.objects.create(
            user=cls.learner_user, institution=cls.school, admission_number="AT-001"
        )
        sibling_user = User.objects.create_user(
            username="attscope_sibling", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.sibling = Learner.objects.create(
            user=sibling_user, institution=cls.school, admission_number="AT-002"
        )
        foreign_user = User.objects.create_user(
            username="attscope_foreign", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.other_school,
        )
        foreign_learner = Learner.objects.create(
            user=foreign_user, institution=cls.other_school, admission_number="AT-999"
        )
        guardian_user = User.objects.create_user(
            username="attscope_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=cls.school,
        )
        cls.guardian_user = guardian_user
        guardian = Guardian.objects.create(user=guardian_user, institution=cls.school)
        cls.link = LearnerGuardian.objects.create(
            learner=cls.learner, guardian=guardian, is_verified=True
        )
        cls.record = AttendanceRecord.objects.create(
            institution=cls.school, learner=cls.learner,
            date=date(2026, 2, 1), status="PRESENT",
        )
        cls.sibling_record = AttendanceRecord.objects.create(
            institution=cls.school, learner=cls.sibling,
            date=date(2026, 2, 1), status="ABSENT",
        )
        cls.foreign_record = AttendanceRecord.objects.create(
            institution=cls.other_school, learner=foreign_learner,
            date=date(2026, 2, 1), status="PRESENT",
        )

    def test_staff_keeps_institution_wide_attendance(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("attendancerecord-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in rows(response)}, {self.record.id, self.sibling_record.id}
        )
        self.assertEqual(
            self.client.get(reverse("attendancerecord-detail", args=[self.foreign_record.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_learner_only_sees_own_attendance(self):
        self.client.force_authenticate(self.learner_user)
        response = self.client.get(reverse("attendancerecord-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.record.id])
        self.assertEqual(
            self.client.get(reverse("attendancerecord-detail", args=[self.sibling_record.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("attendancerecord-detail", args=[self.foreign_record.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_guardian_sees_only_verified_permitted_learner(self):
        self.link.is_verified = False
        self.link.save(update_fields=["is_verified"])
        self.client.force_authenticate(self.guardian_user)
        self.assertEqual(rows(self.client.get(reverse("attendancerecord-list"))), [])

        self.link.is_verified = True
        self.link.can_view_attendance = False
        self.link.save(update_fields=["is_verified", "can_view_attendance"])
        self.assertEqual(rows(self.client.get(reverse("attendancerecord-list"))), [])

        self.link.can_view_attendance = True
        self.link.save(update_fields=["can_view_attendance"])
        response = self.client.get(reverse("attendancerecord-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.record.id])
        self.assertEqual(
            self.client.get(reverse("attendancerecord-detail", args=[self.sibling_record.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("attendancerecord-detail", args=[self.foreign_record.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
