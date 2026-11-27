"""Rubric builder permissions, validation and audit coverage."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.audit import AuditLog
from apps.core.constants import Roles
from apps.curriculum.models import Rubric, RubricLevel
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()
PASSWORD = "StrongPass123!"


class RubricBuilderTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="CUR")
        self.school = Institution.objects.create(
            name="Curriculum School", code="CUR-A", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="curriculum-admin", password=PASSWORD,
            role=Roles.ADMIN, institution=self.school,
        )
        self.client.force_authenticate(user=self.admin)

    def test_school_staff_can_build_a_rubric_and_changes_are_audited(self):
        created = self.client.post(
            reverse("rubric-list"), {"name": "Portrait rubric", "description": "Art work"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        rubric_id = created.data["id"]
        self.assertEqual(created.data["institution"], self.school.pk)

        criterion = self.client.post(
            reverse("rubriccriterion-list"),
            {"rubric": rubric_id, "name": "Composition", "max_score": "10", "sequence": 1},
            format="json",
        )
        self.assertEqual(criterion.status_code, status.HTTP_201_CREATED, criterion.data)

        updated = self.client.patch(
            reverse("rubric-detail", args=[rubric_id]), {"description": "Updated"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        created_audit = AuditLog.objects.get(action="rubric.created", entity_type="Rubric")
        self.assertEqual(created_audit.institution_id, self.school.pk)
        self.assertTrue(AuditLog.objects.filter(action="rubric.updated").exists())
        criterion_audit = AuditLog.objects.get(action="rubric.created", entity_type="RubricCriterion")
        self.assertEqual(criterion_audit.institution_id, self.school.pk)

    def test_global_templates_cannot_be_changed_by_school_users(self):
        global_rubric = Rubric.objects.create(name="National template")
        level = RubricLevel.objects.create(
            rubric=global_rubric, name="Beginning", min_score=0, max_score=40,
        )
        response = self.client.patch(
            reverse("rubriclevel-detail", args=[level.pk]), {"name": "Renamed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bands_must_be_valid_percentages(self):
        rubric = Rubric.objects.create(institution=self.school, name="Essay")
        response = self.client.post(
            reverse("rubriclevel-list"),
            {"rubric": rubric.pk, "name": "Invalid", "min_score": "80", "max_score": "40"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("minimum", str(response.data).lower())

    def test_feedback_comment_bank_is_audited(self):
        response = self.client.post(
            reverse("feedbackcomment-list"),
            {"category": "Writing", "text": "Clear thesis statement."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["created_by"], self.admin.pk)
        self.assertTrue(
            AuditLog.objects.filter(action="feedback_comment.created", entity_type="FeedbackComment").exists()
        )
