"""KICD-style internal review workflow; this does not submit anything to KICD and does not represent official KICD approval."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.approval.models import ApprovalChecklistItem, ApprovalDecision, ApprovalRequest
from apps.content.models import DigitalTextbook, Publisher
from apps.core.constants import ContentStatus, Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


class ApprovalWorkflowTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(
            name="Approval Demo School", code="DEMO01", institution_type=kind,
        )
        self.other_school = Institution.objects.create(
            name="Other School", code="OTHER01", institution_type=kind,
        )
        # Demo usernames only; no passwords are stored or printed.
        self.admin = User.objects.create_user(
            username="demo_admin", password=None,
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )
        self.teacher = User.objects.create_user(
            username="demo_teacher", password=None,
            role=Roles.TEACHER, institution=self.school,
        )
        self.learner = User.objects.create_user(
            username="demo_learner", password=None,
            role=Roles.LEARNER, institution=self.school,
        )
        self.guardian = User.objects.create_user(
            username="demo_guardian", password=None,
            role=Roles.GUARDIAN, institution=self.other_school,
        )
        self.platform_admin = User.objects.create_user(
            username="platform_admin", password=None,
            role=Roles.SUPER_ADMIN, is_staff=True, is_superuser=True,
        )

        publisher = Publisher.objects.create(name="Approval Publisher")
        self.textbook = DigitalTextbook.objects.create(
            title="Approval Textbook", publisher=publisher, isbn="APR-ISBN-001",
            status=ContentStatus.IN_REVIEW,
        )
        self.request = ApprovalRequest.objects.create(
            institution=self.school, title="Grade 4 Mathematics",
            content_type="TEXTBOOK", textbook=self.textbook,
        )

    def _results(self, response):
        return response.data["results"] if isinstance(response.data, dict) else response.data

    def test_lists_are_institution_scoped_and_references_are_generated(self):
        self.assertTrue(self.request.reference.startswith("APR-"))

        self.client.force_authenticate(user=self.guardian)
        response = self.client.get(reverse("approvalrequest-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(response)), 0)
        detail = self.client.get(reverse("approvalrequest-detail", args=[self.request.id]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("approvalrequest-list"))
        self.assertEqual(len(self._results(response)), 1)
        self.assertEqual(self._results(response)[0]["reference"], self.request.reference)

    def test_decision_and_checklist_lists_are_available(self):
        ApprovalDecision.objects.create(
            institution=self.school, request=self.request,
            decision="APPROVE", decided_by=self.admin,
        )
        ApprovalChecklistItem.objects.create(
            institution=self.school, request=self.request, label="Curriculum match",
        )
        self.client.force_authenticate(user=self.admin)
        for name in ("approvaldecision-list", "approvalchecklistitem-list"):
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(self._results(response)), 1)

    def test_learner_cannot_create_requests(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.post(
            reverse("approvalrequest-list"), {"title": "Not allowed"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submit_requires_every_checklist_item_to_be_met(self):
        item = ApprovalChecklistItem.objects.create(
            institution=self.school, request=self.request, label="Complete textbook",
        )
        self.client.force_authenticate(user=self.admin)

        blocked = self.client.post(reverse("approvalrequest-submit", args=[self.request.id]))
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        item.is_met = True
        item.save()
        response = self.client.post(reverse("approvalrequest-submit", args=[self.request.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, "SUBMITTED")
        self.assertEqual(self.request.submitted_by_id, self.admin.id)
        self.assertIsNotNone(self.request.submitted_at)

    def test_forbidden_status_transitions_are_rejected(self):
        self.client.force_authenticate(user=self.admin)
        self.request.status = "APPROVED"
        self.request.save(update_fields=["status", "updated_at"])
        blocked = self.client.post(reverse("approvalrequest-submit", args=[self.request.id]))
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.platform_admin)
        self.request.status = "DRAFT"
        self.request.save(update_fields=["status", "updated_at"])
        blocked = self.client.post(reverse("approvalrequest-publish", args=[self.request.id]))
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_is_curator_only_and_records_a_decision(self):
        self.request.status = "SUBMITTED"
        self.request.save(update_fields=["status", "updated_at"])

        self.client.force_authenticate(user=self.teacher)
        forbidden = self.client.post(
            reverse("approvalrequest-review", args=[self.request.id]),
            {"decision": "APPROVE", "notes": "Teacher review"},
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.platform_admin)
        invalid = self.client.post(
            reverse("approvalrequest-review", args=[self.request.id]),
            {"decision": "MAYBE"},
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("approvalrequest-review", args=[self.request.id]),
            {"decision": "APPROVE", "notes": "Meets the curriculum requirements"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, "APPROVED")
        self.assertEqual(self.request.reviewed_by_id, self.platform_admin.id)
        decision = ApprovalDecision.objects.get(request=self.request)
        self.assertEqual(decision.decision, "APPROVE")
        self.assertEqual(decision.institution_id, self.school.id)
        self.assertEqual(decision.decided_by_id, self.platform_admin.id)

    def test_request_changes_maps_to_changes_requested(self):
        self.request.status = "UNDER_REVIEW"
        self.request.save(update_fields=["status", "updated_at"])
        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.post(
            reverse("approvalrequest-review", args=[self.request.id]),
            {"decision": "REQUEST_CHANGES", "notes": "Add missing outcomes"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, "CHANGES_REQUESTED")

    def test_publish_is_curator_only_and_updates_linked_textbook(self):
        self.request.status = "APPROVED"
        self.request.save(update_fields=["status", "updated_at"])
        url = reverse("approvalrequest-publish", args=[self.request.id])

        self.client.force_authenticate(user=self.admin)
        forbidden = self.client.post(url)
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.request.refresh_from_db()
        self.textbook.refresh_from_db()
        self.assertEqual(self.request.status, "PUBLISHED")
        self.assertEqual(self.textbook.status, ContentStatus.PUBLISHED)

    def test_summary_counts_only_the_callers_scope(self):
        ApprovalRequest.objects.create(
            institution=self.other_school, title="Other school request", status="APPROVED",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("approvalrequest-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["by_status"]["DRAFT"], 1)
        self.assertEqual(response.data["by_status"]["APPROVED"], 0)
        self.assertEqual(response.data["APPROVED"], 0)
