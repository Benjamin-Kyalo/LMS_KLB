"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting.

Automated checks use only the demo usernames already seeded by the project.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.analytics.engine import build_cohorts
from apps.analytics.models import AnalyticsSnapshot, RemediationRule, RemediationTask
from apps.assessments.models import Exam, ExamResult
from apps.attendance.models import AttendanceRecord
from apps.core.constants import MasteryLevel, Roles
from apps.curriculum.models import Competency, CompetencyEvidence, CurriculumFramework
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass, Subject
from apps.learners.models import Learner

User = get_user_model()


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="Analytics Primary", code="ANP")
        self.school = Institution.objects.create(
            name="Analytics School", code="ANAS", institution_type=self.kind
        )
        self.other_school = Institution.objects.create(
            name="Other Analytics School", code="ANOT", institution_type=self.kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.SCHOOL_ADMIN, institution=self.school
        )
        self.teacher = User.objects.create_user(
            username="demo_teacher", role=Roles.TEACHER, institution=self.school
        )
        self.learner_user = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER, institution=self.school
        )
        User.objects.create_user(
            username="demo_guardian", role=Roles.GUARDIAN, institution=self.school
        )
        self.platform = User.objects.create_user(
            username="platform_admin", role=Roles.SUPER_ADMIN,
            is_staff=True, is_superuser=True,
        )
        self.learner = Learner.objects.create(
            user=self.learner_user, institution=self.school, admission_number="ANA-001"
        )
        framework = CurriculumFramework.objects.create(name="CBC", code="CBC", version="1.0")
        self.competency = Competency.objects.create(
            framework=framework, name="Numeracy", code="NUM"
        )
        self.rule = RemediationRule.objects.create(
            institution=self.school,
            name="Low numeracy",
            competency=self.competency,
            mastery_below=Decimal("0.60"),
            min_attempts=1,
            action=RemediationRule.PRACTICE,
        )
        self.client = APIClient()

    def test_list_endpoints_work_and_are_institution_isolated(self):
        own_task = RemediationTask.objects.create(
            institution=self.school, learner=self.learner, rule=self.rule,
            competency=self.competency,
        )
        # The institution scope lives on the task, so a task row can be
        # created for another school to prove the queryset filter works.
        foreign_task = RemediationTask.objects.create(
            institution=self.other_school, learner=self.learner, status=RemediationTask.OPEN
        )
        foreign_rule = RemediationRule.objects.create(
            institution=self.other_school, name="Other school rule"
        )
        foreign_snapshot = AnalyticsSnapshot.objects.create(
            institution=self.other_school, dataset=AnalyticsSnapshot.DASHBOARD,
            period="2026-Term-1",
        )

        self.client.force_authenticate(user=self.admin)
        for name in ("analyticssnapshot-list", "remediationrule-list", "remediationtask-list"):
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        task_ids = [row["id"] for row in self.client.get(reverse("remediationtask-list")).data["results"]]
        self.assertIn(own_task.id, task_ids)
        self.assertNotIn(foreign_task.id, task_ids)
        rule_ids = [row["id"] for row in self.client.get(reverse("remediationrule-list")).data["results"]]
        self.assertIn(self.rule.id, rule_ids)
        self.assertNotIn(foreign_rule.id, rule_ids)
        snapshot_ids = [
            row["id"] for row in self.client.get(reverse("analyticssnapshot-list")).data["results"]
        ]
        self.assertNotIn(foreign_snapshot.id, snapshot_ids)

    def test_rule_evaluation_is_idempotent_and_never_reopens_closed_tasks(self):
        CompetencyEvidence.objects.create(
            institution=self.school, learner=self.learner, competency=self.competency,
            achieved_level=MasteryLevel.BEGINNING,
        )
        url = reverse("analytics-remediation-evaluate")
        self.client.force_authenticate(user=self.teacher)

        first = self.client.post(url, {}, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK, first.data)
        self.assertEqual(first.data["created"], 1)
        self.assertEqual(first.data["updated"], 0)

        second = self.client.post(url, {}, format="json")
        self.assertEqual(second.status_code, status.HTTP_200_OK, second.data)
        self.assertEqual(second.data["created"], 0)
        self.assertEqual(second.data["updated"], 1)
        self.assertEqual(RemediationTask.objects.filter(institution=self.school).count(), 1)

        task = RemediationTask.objects.get(institution=self.school)
        self.assertEqual(task.status, RemediationTask.OPEN)
        self.assertIn("competency_evidence", task.evidence["signals"])
        self.assertEqual(task.evidence["signals"]["competency_evidence"]["attempts"], 1)

        task.status = RemediationTask.COMPLETED
        task.save()
        third = self.client.post(url, {}, format="json")
        self.assertEqual(third.data["skipped"], 1)
        task.refresh_from_db()
        self.assertEqual(task.status, RemediationTask.COMPLETED)
        self.assertEqual(RemediationTask.objects.count(), 1)

    def test_learner_only_sees_and_updates_own_support_tasks(self):
        own_task = RemediationTask.objects.create(
            institution=self.school, learner=self.learner, rule=self.rule,
            competency=self.competency,
        )
        other_user = User.objects.create_user(
            username="analytics_other_learner",
            role=Roles.LEARNER,
            institution=self.school,
        )
        other_learner = Learner.objects.create(
            user=other_user, institution=self.school, admission_number="ANA-002"
        )
        other_task = RemediationTask.objects.create(
            institution=self.school, learner=other_learner, rule=self.rule,
        )

        self.client.force_authenticate(user=self.learner_user)
        listed = self.client.get(reverse("analytics-my-tasks"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK, listed.data)
        ids = [row["id"] for row in listed.data]
        self.assertIn(own_task.id, ids)
        self.assertNotIn(other_task.id, ids)
        self.assertEqual(listed.data[0]["rule_name"], self.rule.name)

        completed = self.client.post(
            reverse("analytics-my-task-complete", args=[own_task.id]), {}, format="json"
        )
        self.assertEqual(completed.status_code, status.HTTP_200_OK, completed.data)
        self.assertEqual(completed.data["status"], RemediationTask.COMPLETED)
        self.assertIsNotNone(completed.data["resolved_at"])

        forbidden = self.client.post(
            reverse("analytics-my-task-dismiss", args=[other_task.id]), {}, format="json"
        )
        self.assertEqual(forbidden.status_code, status.HTTP_404_NOT_FOUND, forbidden.data)

        guardian = User.objects.get(username="demo_guardian")
        self.client.force_authenticate(user=guardian)
        self.assertEqual(
            self.client.get(reverse("analytics-my-tasks")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_forbidden_writes_return_403(self):
        task = RemediationTask.objects.create(
            institution=self.school, learner=self.learner, rule=self.rule,
            competency=self.competency,
        )
        rule_url = reverse("remediationrule-list")
        task_url = reverse("remediationtask-detail", args=[task.id])

        self.client.force_authenticate(user=self.learner_user)
        self.assertEqual(
            self.client.post(rule_url, {"name": "Nope"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.patch(task_url, {"status": "COMPLETED"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(
            self.client.post(rule_url, {"name": "Teacher rule"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_function_endpoints_and_snapshot_refresh(self):
        self.client.force_authenticate(user=self.admin)
        dashboard = self.client.get(reverse("analytics-dashboard"))
        self.assertEqual(dashboard.status_code, status.HTTP_200_OK, dashboard.data)
        self.assertEqual(dashboard.data["total_learners"], 1)
        self.assertIsNone(dashboard.data["attendance_rate_percent"])

        cohorts = self.client.get(reverse("analytics-cohorts"))
        self.assertEqual(cohorts.status_code, status.HTTP_200_OK, cohorts.data)
        self.assertIsInstance(cohorts.data, list)

        summary = self.client.get(reverse("analytics-remediation-summary"))
        self.assertEqual(summary.status_code, status.HTTP_200_OK, summary.data)
        self.assertEqual(summary.data["active_rules"], 1)
        self.assertEqual(summary.data["by_status"]["OPEN"], 0)

        url = reverse("analytics-snapshots-refresh")
        payload = {"dataset": "DASHBOARD", "period": "2026-Term-1"}
        first = self.client.post(url, payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        self.assertTrue(first.data["reference"].startswith("ANA"))
        second = self.client.post(url, payload, format="json")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED, second.data)
        self.assertEqual(AnalyticsSnapshot.objects.count(), 1)
        self.assertEqual(
            AnalyticsSnapshot.objects.get().payload["total_learners"], 1
        )

        self.client.force_authenticate(user=self.learner_user)
        self.assertEqual(
            self.client.get(reverse("analytics-dashboard")).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(url, payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # A platform user without a school never receives a platform-wide view.
        self.client.force_authenticate(user=self.platform)
        self.assertEqual(
            self.client.get(reverse("analytics-dashboard")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_task_actions_and_rule_toggle(self):
        task = RemediationTask.objects.create(
            institution=self.school, learner=self.learner, rule=self.rule,
            competency=self.competency,
        )
        self.client.force_authenticate(user=self.teacher)
        assigned = self.client.post(
            reverse("remediationtask-assign", args=[task.id]),
            {"user_id": self.teacher.id}, format="json",
        )
        self.assertEqual(assigned.status_code, status.HTTP_200_OK, assigned.data)
        self.assertEqual(assigned.data["status"], RemediationTask.ASSIGNED)

        completed = self.client.post(reverse("remediationtask-complete", args=[task.id]), {}, format="json")
        self.assertEqual(completed.status_code, status.HTTP_200_OK, completed.data)
        self.assertEqual(completed.data["status"], RemediationTask.COMPLETED)
        self.assertIsNotNone(completed.data["resolved_at"])

        dismissed = self.client.post(reverse("remediationtask-dismiss", args=[task.id]), {}, format="json")
        self.assertEqual(dismissed.status_code, status.HTTP_200_OK, dismissed.data)
        self.assertEqual(dismissed.data["status"], RemediationTask.DISMISSED)

        self.client.force_authenticate(user=self.admin)
        toggled = self.client.patch(reverse("remediationrule-toggle", args=[self.rule.id]), {}, format="json")
        self.assertEqual(toggled.status_code, status.HTTP_200_OK, toggled.data)
        self.assertFalse(toggled.data["is_active"])
        self.rule.refresh_from_db()
        self.assertFalse(self.rule.is_active)

    def test_cohorts_use_only_existing_records(self):
        year = AcademicYear.objects.create(
            institution=self.school, name="2026",
            start_date=date(2026, 1, 5), end_date=date(2026, 12, 20),
        )
        school_class = SchoolClass.objects.create(
            institution=self.school, academic_year=year, name="Grade 4"
        )
        subject = Subject.objects.create(institution=self.school, name="Mathematics")
        self.learner.class_room = school_class
        self.learner.save()
        exam = Exam.objects.create(
            title="Term 1 Mathematics", institution=self.school,
            subject=subject, exam_date=date(2026, 3, 20), max_score=100,
        )
        ExamResult.objects.create(
            exam=exam, learner=self.learner, institution=self.school, score=80
        )
        for offset, record_status in enumerate(["PRESENT", "ABSENT"]):
            AttendanceRecord.objects.create(
                learner=self.learner, institution=self.school,
                date=date(2026, 3, 20 + offset), status=record_status,
            )

        rows = build_cohorts(self.school, {"class_room_id": school_class.id})
        row = next(item for item in rows if item["subject_id"] == subject.id)
        self.assertEqual(row["class"], "Grade 4")
        self.assertEqual(row["subject"], "Mathematics")
        self.assertEqual(row["learners"], 1)
        self.assertEqual(row["attendance_percentage"], 50.0)
        self.assertEqual(row["result_average"], 80.0)
        self.assertIsNone(row["average_mastery"])
