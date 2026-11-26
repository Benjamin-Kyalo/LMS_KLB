"""Rule-based early warning and intervention task checks."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.analytics.models import InterventionTask
from apps.assessments.models import Exam, ExamResult
from apps.attendance.models import AttendanceRecord
from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


class EarlyWarningTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Warning Primary", code="WRP")
        self.school = Institution.objects.create(
            name="Warning School", code="WARN", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN, institution=self.school
        )
        self.teacher = User.objects.create_user(
            username="demo_teacher", role=Roles.TEACHER, institution=self.school
        )
        learner_user = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER, institution=self.school
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="WARN-001"
        )
        today = timezone.localdate()
        for offset in range(6):
            AttendanceRecord.objects.create(
                institution=self.school, learner=self.learner,
                date=today - timedelta(days=offset),
                status="ABSENT" if offset < 4 else "PRESENT",
            )
        exam = Exam.objects.create(
            institution=self.school, title="Term test", max_score=Decimal("100")
        )
        ExamResult.objects.create(
            institution=self.school, exam=exam, learner=self.learner, score=Decimal("35")
        )
        self.client = APIClient()

    def test_flags_are_explained_and_staff_only(self):
        url = reverse("analytics-early-warning")
        self.client.force_authenticate(user=self.learner.user)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["summary"]["high"], 1)
        alert = response.data["alerts"][0]
        self.assertEqual(alert["risk_level"], "HIGH")
        codes = {signal["code"] for signal in alert["signals"]}
        self.assertIn("ATTENDANCE", codes)
        self.assertIn("ASSESSMENT", codes)
        self.assertTrue(all("detail" in signal for signal in alert["signals"]))
        self.assertTrue(response.data["rules"]["ATTENDANCE"]["absent_rate_above"] == 0.20)

    def test_refresh_creates_one_task_and_task_can_be_resolved(self):
        refresh_url = reverse("analytics-early-warning-refresh")
        self.client.force_authenticate(user=self.teacher)
        first = self.client.post(refresh_url, {}, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK, first.data)
        self.assertEqual(first.data["tasks_created"], 1)
        second = self.client.post(refresh_url, {}, format="json")
        self.assertEqual(second.data["tasks_created"], 0)
        self.assertEqual(InterventionTask.objects.filter(learner=self.learner).count(), 1)

        task = InterventionTask.objects.get(learner=self.learner)
        self.assertEqual(task.risk_level, "HIGH")
        self.assertEqual(len(task.signals), 2)
        assign = self.client.post(
            reverse("interventiontask-assign", args=[task.pk]),
            {"user_id": self.teacher.pk}, format="json",
        )
        self.assertEqual(assign.status_code, status.HTTP_200_OK, assign.data)
        self.assertEqual(assign.data["status"], "ASSIGNED")
        complete = self.client.post(
            reverse("interventiontask-complete", args=[task.pk]), {}, format="json"
        )
        self.assertEqual(complete.data["status"], "COMPLETED")
        self.assertTrue(complete.data["resolved_at"])
