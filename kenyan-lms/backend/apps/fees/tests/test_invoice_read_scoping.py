"""Fee invoice read scoping: staff, learner and guardian families."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.fees.models import FeeInvoice
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


def rows(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class InvoiceReadScopingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        kind = InstitutionType.objects.create(name="Fee Scope Primary", code="FSP")
        cls.school = Institution.objects.create(
            name="Fee Scope School", code="FSCOPE", institution_type=kind
        )
        cls.other_school = Institution.objects.create(
            name="Fee Scope Other", code="FSCOPE2", institution_type=kind
        )
        cls.admin = User.objects.create_user(
            username="feescope_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=cls.school,
        )
        cls.learner_user = User.objects.create_user(
            username="feescope_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.learner = Learner.objects.create(
            user=cls.learner_user, institution=cls.school, admission_number="FS-001"
        )
        sibling_user = User.objects.create_user(
            username="feescope_sibling", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.sibling = Learner.objects.create(
            user=sibling_user, institution=cls.school, admission_number="FS-002"
        )
        foreign_user = User.objects.create_user(
            username="feescope_foreign", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.other_school,
        )
        foreign_learner = Learner.objects.create(
            user=foreign_user, institution=cls.other_school, admission_number="FS-999"
        )
        guardian_user = User.objects.create_user(
            username="feescope_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=cls.school,
        )
        cls.guardian_user = guardian_user
        guardian = Guardian.objects.create(user=guardian_user, institution=cls.school)
        cls.link = LearnerGuardian.objects.create(
            learner=cls.learner, guardian=guardian,
            is_verified=True, can_view_fees=False,
        )
        cls.invoice = FeeInvoice.objects.create(
            institution=cls.school, learner=cls.learner,
            amount_due="100.00", issue_date=date(2026, 1, 1),
        )
        cls.sibling_invoice = FeeInvoice.objects.create(
            institution=cls.school, learner=cls.sibling,
            amount_due="200.00", issue_date=date(2026, 1, 2),
        )
        cls.foreign_invoice = FeeInvoice.objects.create(
            institution=cls.other_school, learner=foreign_learner,
            amount_due="300.00", issue_date=date(2026, 1, 3),
        )

    def test_staff_keeps_institution_wide_invoices(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("feeinvoice-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in rows(response)}, {self.invoice.id, self.sibling_invoice.id}
        )
        self.assertEqual(
            self.client.get(reverse("feeinvoice-detail", args=[self.foreign_invoice.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        summary = self.client.get(reverse("feeinvoice-summary"))
        self.assertEqual(summary.data["invoices"], 2)

    def test_learner_only_sees_own_invoices(self):
        self.client.force_authenticate(self.learner_user)
        response = self.client.get(reverse("feeinvoice-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.invoice.id])
        self.assertEqual(
            self.client.get(reverse("feeinvoice-detail", args=[self.sibling_invoice.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("feeinvoice-detail", args=[self.foreign_invoice.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        # The portal endpoint stays scoped to the same family.
        portal = self.client.get(reverse("fee-my-invoices"))
        self.assertEqual([row["id"] for row in portal.data["results"]], [self.invoice.id])

    def test_guardian_needs_verified_link_and_fees_permission(self):
        self.client.force_authenticate(self.guardian_user)
        self.assertEqual(rows(self.client.get(reverse("feeinvoice-list"))), [])
        self.assertEqual(self.client.get(reverse("fee-my-invoices")).data["count"], 0)

        self.link.can_view_fees = True
        self.link.save(update_fields=["can_view_fees"])
        response = self.client.get(reverse("feeinvoice-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.invoice.id])
        self.assertEqual(
            self.client.get(reverse("feeinvoice-detail", args=[self.sibling_invoice.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(reverse("feeinvoice-detail", args=[self.foreign_invoice.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        portal = self.client.get(reverse("fee-my-invoices"))
        self.assertEqual([row["id"] for row in portal.data["results"]], [self.invoice.id])

        self.link.is_verified = False
        self.link.save(update_fields=["is_verified"])
        self.assertEqual(rows(self.client.get(reverse("feeinvoice-list"))), [])
        self.assertEqual(self.client.get(reverse("fee-my-invoices")).data["count"], 0)
