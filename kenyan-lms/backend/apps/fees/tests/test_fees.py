"""Fee ledger API tests: isolation, permission and payment arithmetic."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.fees.models import FeeInvoice, FeeStructure, Payment
from apps.guardians.models import Guardian
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass, Term
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


class FeeTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.institution_type = InstitutionType.objects.create(name="Secondary", code="SEC")
        cls.school_a = Institution.objects.create(
            name="Fee Test School A", code="FEETESTA", institution_type=cls.institution_type
        )
        cls.school_b = Institution.objects.create(
            name="Fee Test School B", code="FEETESTB", institution_type=cls.institution_type
        )
        cls.admin_a = User.objects.create_user(
            username="fee_admin_a", password="not-a-real-password",
            role=Roles.ADMIN, institution=cls.school_a,
        )
        cls.admin_b = User.objects.create_user(
            username="fee_admin_b", password="not-a-real-password",
            role=Roles.ADMIN, institution=cls.school_b,
        )
        cls.learner_user = User.objects.create_user(
            username="fee_learner", password="not-a-real-password",
            role=Roles.LEARNER, institution=cls.school_a,
        )
        cls.learner = Learner.objects.create(
            user=cls.learner_user, institution=cls.school_a, admission_number="FEE-001"
        )
        cls.guardian_user = User.objects.create_user(
            username="fee_guardian", password="not-a-real-password",
            role=Roles.GUARDIAN, institution=cls.school_a,
        )
        cls.guardian = Guardian.objects.create(user=cls.guardian_user, institution=cls.school_a)
        cls.year = AcademicYear.objects.create(
            institution=cls.school_a, name="2026", start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        cls.term = Term.objects.create(
            institution=cls.school_a, academic_year=cls.year, name="Term 1",
            start_date=date(2026, 1, 1), end_date=date(2026, 4, 30),
        )
        cls.school_class = SchoolClass.objects.create(
            institution=cls.school_a, academic_year=cls.year, name="Form 1"
        )
        cls.structure = FeeStructure.objects.create(
            institution=cls.school_a, name="Tuition", term=cls.term,
            school_class=cls.school_class, amount="1000.00",
        )
        cls.other_structure = FeeStructure.objects.create(
            institution=cls.school_b, name="Tuition", term=cls.term, amount="2000.00"
        )
        cls.invoice = FeeInvoice.objects.create(
            institution=cls.school_a, learner=cls.learner, fee_structure=cls.structure,
            amount_due="1000.00", issue_date=date(2026, 1, 10),
        )

    def test_structure_list_is_scoped_to_institution(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get(reverse("feestructure-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [row["name"] for row in response.data["results"]]
        self.assertIn("Tuition", names)
        self.assertEqual(len(response.data["results"]), 1)

    def test_learner_cannot_create_a_fee_structure(self):
        self.client.force_authenticate(self.learner_user)
        response = self.client.post(reverse("feestructure-list"), {
            "name": "Illegal", "term": self.term.pk, "amount": "10.00",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_and_payment_references_and_totals(self):
        self.client.force_authenticate(self.admin_a)
        created = self.client.post(reverse("feeinvoice-list"), {
            "learner": self.learner.pk, "fee_structure": self.structure.pk,
            "amount_due": "500.00", "issue_date": "2026-02-01",
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertTrue(created.data["reference"].startswith("INV-"))

        paid = self.client.post(reverse("payment-list"), {
            "invoice": created.data["id"], "amount": "200.00",
            "method": "MOBILE", "paid_at": timezone.now().isoformat(),
        }, format="json")
        self.assertEqual(paid.status_code, status.HTTP_201_CREATED)
        self.assertTrue(paid.data["reference"].startswith("PAY-"))

        invoice = FeeInvoice.objects.get(pk=created.data["id"])
        self.assertEqual(str(invoice.amount_paid), "200.00")
        self.assertEqual(invoice.status, "PARTIAL")
        self.assertEqual(str(invoice.balance), "300.00")

    def test_guardian_fees_require_explicit_permission(self):
        self.client.force_authenticate(self.guardian_user)
        response = self.client.get(reverse("fee-my-invoices"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        LearnerGuardian.objects.create(
            learner=self.learner, guardian=self.guardian, can_view_fees=True
        )
        response = self.client.get(reverse("fee-my-invoices"))
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.invoice.pk)

    def test_payment_for_another_schools_invoice_is_forbidden(self):
        other_invoice = FeeInvoice.objects.create(
            institution=self.school_b, learner=self.learner,
            amount_due="50.00", issue_date=date(2026, 1, 1),
        )
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(reverse("payment-list"), {
            "invoice": other_invoice.pk, "amount": "50.00", "method": "CASH",
            "paid_at": timezone.now().isoformat(),
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Payment.objects.filter(invoice=other_invoice).exists())
