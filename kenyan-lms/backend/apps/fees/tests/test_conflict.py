"""Conflict replay tests: duplicate writes and stale updates return structured 409s."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.fees.models import FeeStructure
from apps.institutions.models import AcademicYear, Institution, InstitutionType, Term

User = get_user_model()


class ConflictTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        kind = InstitutionType.objects.create(name="Conflict Secondary", code="CFLSEC")
        cls.school = Institution.objects.create(
            name="Conflict School", code="CFLTEST", institution_type=kind
        )
        cls.admin = User.objects.create_user(
            username="conflict_admin", password="not-a-real-password",
            role=Roles.ADMIN, institution=cls.school,
        )
        year = AcademicYear.objects.create(
            institution=cls.school, name="2026", start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        cls.term = Term.objects.create(
            institution=cls.school, academic_year=year, name="Term 1",
            start_date=date(2026, 1, 1), end_date=date(2026, 4, 30),
        )
        cls.structure = FeeStructure.objects.create(
            institution=cls.school, name="Activity", term=cls.term, amount="250.00"
        )

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def test_duplicate_create_returns_structured_conflict(self):
        response = self.client.post(reverse("feestructure-list"), {
            "name": "Activity", "term": self.term.pk, "amount": "250.00",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "conflict")
        self.assertNotIn("duplicate key", str(response.data).lower())

    def test_stale_if_match_returns_server_copy(self):
        self.structure.refresh_from_db()
        stale_token = self.structure.updated_at.isoformat()
        FeeStructure.objects.filter(pk=self.structure.pk).update(
            amount="400.00", updated_at=timezone.now()
        )
        self.structure.refresh_from_db()

        response = self.client.patch(
            reverse("feestructure-detail", args=[self.structure.pk]),
            {"amount": "300.00"}, format="json", HTTP_IF_MATCH=stale_token,
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "conflict")
        self.assertEqual(str(response.data["server"]["data"]["amount"]), "400.00")

    def test_matching_if_match_is_accepted(self):
        self.structure.refresh_from_db()
        token = self.structure.updated_at.isoformat()
        response = self.client.patch(
            reverse("feestructure-detail", args=[self.structure.pk]),
            {"amount": "300.00"}, format="json", HTTP_IF_MATCH=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.structure.refresh_from_db()
        self.assertEqual(str(self.structure.amount), "300.00")
