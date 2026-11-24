"""Automated checks for dashboards, analytics and report permissions."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessments.models import Exam, ExamResult
from apps.attendance.models import AttendanceRecord
from apps.core.constants import Roles
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


class ReportTests(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="Basic Education")
        self.school = Institution.objects.create(
            name="Analytics Demo School", institution_type=self.kind
        )
        self.other_school = Institution.objects.create(
            name="Other Demo School", institution_type=self.kind
        )
        self.admin = User.objects.create_user(
            username="report_admin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )
        self.learner_user = User.objects.create_user(
            username="report_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=self.learner_user, institution=self.school,
            admission_number="ANA-001",
        )
        self.exam = Exam.objects.create(
            title="Term 1 Mathematics", institution=self.school,
            exam_date=date(2026, 3, 20), max_score=100,
        )
        ExamResult.objects.create(
            exam=self.exam, learner=self.learner, institution=self.school, score=78
        )
        for offset, record_status in enumerate(["PRESENT", "PRESENT", "LATE", "ABSENT"]):
            AttendanceRecord.objects.create(
                learner=self.learner, institution=self.school,
                date=date(2026, 3, 20 + offset), status=record_status,
            )

    def test_dashboard_returns_fixed_categories_and_staff_only_access(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("school-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_learners"], 1)
        self.assertEqual(response.data["attendance_rate_percent"], 50.0)
        self.assertEqual(response.data["attendance_breakdown"]["EXCUSED"], 0)
        self.assertEqual(response.data["average_exam_score"], 78.0)

        self.client.force_authenticate(user=self.learner_user)
        self.assertEqual(
            self.client.get(reverse("school-dashboard")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_dashboard_does_not_fail_open_for_institutionless_staff(self):
        drifter = User.objects.create_user(
            username="no_school_admin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN,
        )
        self.client.force_authenticate(user=drifter)
        response = self.client.get(reverse("school-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_learners"], 0)

    def test_analytics_returns_chart_ready_series(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("report-analytics"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["attendance_status"]), 4)
        self.assertEqual(
            [item["status"] for item in response.data["attendance_status"]],
            ["PRESENT", "ABSENT", "LATE", "EXCUSED"],
        )
        self.assertEqual(len(response.data["attendance_trend"]), 4)
        self.assertEqual(response.data["exam_results"][0]["score"], 78.0)
        self.assertEqual(response.data["performance_by_class"][0]["class"], "Unassigned")
        self.assertEqual(response.data["learner_status"][0]["value"], 1)

    def test_learner_can_open_own_report_but_not_another(self):
        self.client.force_authenticate(user=self.learner_user)
        response = self.client.get(reverse("learner-report", args=[self.learner.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_score"], 78.0)

        other_user = User.objects.create_user(
            username="other_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.other_school,
        )
        other = Learner.objects.create(
            user=other_user, institution=self.other_school, admission_number="OTH-001"
        )
        self.assertEqual(
            self.client.get(reverse("learner-report", args=[other.id])).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guardian_permissions_are_respected(self):
        guardian_user = User.objects.create_user(
            username="report_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=self.school,
        )
        guardian = Guardian.objects.create(user=guardian_user, institution=self.school)
        LearnerGuardian.objects.create(
            learner=self.learner, guardian=guardian,
            can_view_academics=False, can_view_attendance=True,
        )
        self.client.force_authenticate(user=guardian_user)
        picker = self.client.get(reverse("report-my-learners"))
        self.assertEqual([item["id"] for item in picker.data], [self.learner.id])
        response = self.client.get(reverse("learner-report", args=[self.learner.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exams"], [])
        self.assertIsNone(response.data["average_score"])
        self.assertGreater(response.data["attendance"]["PRESENT"], 0)

    def test_attendance_create_injects_institution(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("attendancerecord-list"), {
            "learner": self.learner.id,
            "date": "2026-04-01",
            "status": "PRESENT",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        record = AttendanceRecord.objects.get(learner=self.learner, date="2026-04-01")
        self.assertEqual(record.institution_id, self.school.id)

    def test_platform_admin_cannot_create_orphan_snapshot(self):
        platform = User.objects.create_user(
            username="report_platform", password="StrongPass123!",
            role=Roles.SUPER_ADMIN,
        )
        self.client.force_authenticate(user=platform)
        response = self.client.post(reverse("reportssnapshot-list"), {
            "title": "Global report", "report_type": "ATTENDANCE", "data": {},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("institution", str(response.data))
