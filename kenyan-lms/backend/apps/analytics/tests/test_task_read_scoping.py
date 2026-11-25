"""Remediation task read scoping for staff, learners and guardians."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import RemediationTask
from apps.core.constants import Roles
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


def rows(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class RemediationTaskReadScopingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        kind = InstitutionType.objects.create(name="Task Scope", code="RTS")
        cls.school = Institution.objects.create(
            name="Task School", code="RTSCOPE", institution_type=kind
        )
        cls.other_school = Institution.objects.create(
            name="Task Other", code="RTSCOPE2", institution_type=kind
        )
        cls.admin = User.objects.create_user(
            username="rtscope_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=cls.school,
        )
        cls.learner_user = User.objects.create_user(
            username="rtscope_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.learner = Learner.objects.create(
            user=cls.learner_user, institution=cls.school, admission_number="RT-001"
        )
        sibling_user = User.objects.create_user(
            username="rtscope_sibling", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        sibling = Learner.objects.create(
            user=sibling_user, institution=cls.school, admission_number="RT-002"
        )
        foreign_user = User.objects.create_user(
            username="rtscope_foreign", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.other_school,
        )
        foreign_learner = Learner.objects.create(
            user=foreign_user, institution=cls.other_school, admission_number="RT-999"
        )
        guardian_user = User.objects.create_user(
            username="rtscope_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=cls.school,
        )
        cls.guardian_user = guardian_user
        guardian = Guardian.objects.create(user=guardian_user, institution=cls.school)
        cls.link = LearnerGuardian.objects.create(
            learner=cls.learner, guardian=guardian, is_verified=True
        )
        cls.task = RemediationTask.objects.create(
            institution=cls.school, learner=cls.learner
        )
        cls.sibling_task = RemediationTask.objects.create(
            institution=cls.school, learner=sibling
        )
        cls.foreign_task = RemediationTask.objects.create(
            institution=cls.other_school, learner=foreign_learner
        )

    def test_staff_keeps_institution_wide_tasks(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("remediationtask-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in rows(response)}, {self.task.id, self.sibling_task.id}
        )
        self.assertEqual(
            self.client.get(reverse("remediationtask-detail", args=[self.foreign_task.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_learner_sees_only_own_tasks(self):
        self.client.force_authenticate(self.learner_user)
        response = self.client.get(reverse("remediationtask-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.task.id])
        self.assertEqual(
            self.client.get(reverse("remediationtask-detail", args=[self.sibling_task.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("remediationtask-detail", args=[self.foreign_task.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_guardian_sees_only_verified_academic_links(self):
        self.link.is_verified = False
        self.link.save(update_fields=["is_verified"])
        self.client.force_authenticate(self.guardian_user)
        self.assertEqual(rows(self.client.get(reverse("remediationtask-list"))), [])

        self.link.is_verified = True
        self.link.can_view_academics = False
        self.link.save(update_fields=["is_verified", "can_view_academics"])
        self.assertEqual(rows(self.client.get(reverse("remediationtask-list"))), [])

        self.link.can_view_academics = True
        self.link.save(update_fields=["can_view_academics"])
        response = self.client.get(reverse("remediationtask-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.task.id])
        self.assertEqual(
            self.client.get(reverse("remediationtask-detail", args=[self.sibling_task.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("remediationtask-detail", args=[self.foreign_task.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_learner_portal_task_endpoints_stay_learner_only(self):
        self.client.force_authenticate(self.guardian_user)
        self.assertEqual(
            self.client.get(reverse("analytics-my-tasks")).status_code,
            status.HTTP_403_FORBIDDEN,
        )
