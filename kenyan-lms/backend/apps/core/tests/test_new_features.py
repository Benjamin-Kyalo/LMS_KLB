"""Audit history and data-quality console checks."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.audit import log_audit
from apps.core.constants import Roles
from apps.core.models import AuditLog
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


class AuditAndQualityTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Quality Primary", code="QLP")
        self.school = Institution.objects.create(
            name="Quality School", code="QUAL", institution_type=kind
        )
        self.other_school = Institution.objects.create(
            name="Other Quality School", code="QALT", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN, institution=self.school
        )
        self.learner_user = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER, institution=self.school
        )
        self.learner = Learner.objects.create(
            user=self.learner_user, institution=self.school,
            admission_number="  qual-001  ", date_admitted=None,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_audit_api_is_read_only_and_institution_scoped(self):
        own = log_audit(
            self.admin, "test.action", "Learner", self.learner.pk,
            {"changed_fields": ["first_name"]}, institution=self.school,
        )
        foreign = log_audit(
            self.admin, "test.action", "Learner", 999, institution=self.other_school
        )
        response = self.client.get(reverse("auditlog-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(own.pk, ids)
        self.assertNotIn(foreign.pk, ids)
        row = next(item for item in response.data["results"] if item["id"] == own.pk)
        self.assertEqual(row["actor_name"], self.admin.full_name)
        self.assertEqual(row["details"]["changed_fields"], ["first_name"])
        self.assertEqual(
            self.client.post(reverse("auditlog-list"), {}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_field_level_history_records_identity_changes(self):
        response = self.client.patch(
            reverse("learner-detail", args=[self.learner.pk]),
            {"first_name": "Updated", "assessment_number": "ASSESS-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        entry = AuditLog.objects.filter(action="learner.updated").first()
        self.assertIsNotNone(entry)
        self.assertIn("first_name", entry.details["changed_fields"])
        self.assertEqual(entry.details["after"]["first_name"], "Updated")
        self.assertNotIn("password", entry.details["before"])

    def test_scan_previews_and_applies_only_safe_fixes(self):
        scan_url = reverse("core-data-quality")
        scan = self.client.get(scan_url)
        self.assertEqual(scan.status_code, status.HTTP_200_OK, scan.data)
        codes = {item["code"] for item in scan.data["issues"]}
        self.assertIn("identifier_whitespace", codes)
        self.assertIn("learner_admitted_date", codes)
        whitespace = next(item for item in scan.data["issues"] if item["code"] == "identifier_whitespace")
        self.assertEqual(whitespace["count"], 1)

        fix_url = reverse("core-data-quality-fix")
        preview = self.client.post(
            fix_url, {"issue_type": "identifier_whitespace"}, format="json"
        )
        self.assertEqual(preview.status_code, status.HTTP_200_OK, preview.data)
        self.assertFalse(preview.data["applied"])
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.admission_number, "  qual-001  ")

        rejected = self.client.post(
            fix_url, {"issue_type": "delete_duplicates", "confirm": True}, format="json"
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)

        applied = self.client.post(
            fix_url, {"issue_type": "identifier_whitespace", "confirm": True}, format="json"
        )
        self.assertEqual(applied.status_code, status.HTTP_200_OK, applied.data)
        self.assertTrue(applied.data["applied"])
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.admission_number, "qual-001")
        self.assertTrue(
            AuditLog.objects.filter(action="data_quality.fixed").exists()
        )

        applied_dates = self.client.post(
            fix_url, {"issue_type": "learner_admitted_date", "confirm": True}, format="json"
        )
        self.assertEqual(applied_dates.status_code, status.HTTP_200_OK, applied_dates.data)
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.date_admitted, date.today())
