"""M-Pesa-ready receipt and reconciliation checks."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.communications.models import Notification
from apps.core.constants import Roles
from apps.fees.models import FeeInvoice, Payment
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian
from apps.guardians.models import Guardian

User = get_user_model()


class ReceiptTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Receipt Primary", code="RCP")
        self.school = Institution.objects.create(
            name="Receipt School", code="RECP", institution_type=kind
        )
        self.admin = User.objects.create_user(
            username="demo_admin", role=Roles.ADMIN, institution=self.school
        )
        learner_user = User.objects.create_user(
            username="demo_learner", role=Roles.LEARNER, institution=self.school
        )
        guardian_user = User.objects.create_user(
            username="demo_guardian", role=Roles.GUARDIAN, institution=self.school
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="RCP-001"
        )
        guardian = Guardian.objects.create(
            user=guardian_user, institution=self.school, guardian_number="G-RCP-001"
        )
        LearnerGuardian.objects.create(
            learner=self.learner, guardian=guardian, is_verified=True, can_view_fees=True
        )
        self.invoice = FeeInvoice.objects.create(
            institution=self.school, learner=self.learner,
            amount_due=1200, issue_date=date.today(),
            due_date=date.today() - timedelta(days=10),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_mobile_payment_receipt_and_reconciliation(self):
        response = self.client.post(reverse("payment-list"), {
            "invoice": self.invoice.pk,
            "amount": "500.00",
            "method": "MOBILE",
            "paid_at": "2026-11-20T10:00:00Z",
            "payer_phone": "0712345678",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["reconciliation_status"], "EXCEPTION")
        payment = Payment.objects.get(pk=response.data["id"])
        self.assertTrue(payment.reference)
        self.assertEqual(self.invoice.payments.count(), 1)

        guardian_notice = Notification.objects.filter(recipient=self.admin).count()
        self.assertEqual(guardian_notice, 0)
        self.assertTrue(Notification.objects.filter(recipient__username="demo_guardian").exists())

        receipt = self.client.get(reverse("payment-receipt", args=[payment.pk]))
        self.assertEqual(receipt.status_code, status.HTTP_200_OK, receipt.data)
        self.assertEqual(receipt.data["receipt_number"], payment.reference)
        self.assertEqual(receipt.data["school_name"], self.school.name)
        self.assertEqual(receipt.data["learner_name"], self.learner.user.full_name)

        exceptions = self.client.get(reverse("fee-reconciliation"))
        self.assertEqual(exceptions.status_code, status.HTTP_200_OK, exceptions.data)
        self.assertEqual(exceptions.data["counts"]["missing_reference"], 1)
        self.assertTrue(
            any(item["reason"] == "MISSING_TRANSACTION_REFERENCE" for item in exceptions.data["exceptions"])
        )

        rejected = self.client.post(reverse("payment-reconcile", args=[payment.pk]), {}, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        reconciled = self.client.post(
            reverse("payment-reconcile", args=[payment.pk]),
            {"transaction_reference": "SEED1234"}, format="json",
        )
        self.assertEqual(reconciled.status_code, status.HTTP_200_OK, reconciled.data)
        payment.refresh_from_db()
        self.assertEqual(payment.reconciliation_status, "RECONCILED")
        self.assertEqual(payment.transaction_reference, "SEED1234")

    def test_duplicate_transaction_code_is_rejected(self):
        Payment.objects.create(
            institution=self.school, invoice=self.invoice, amount=100,
            method="MOBILE", paid_at="2026-11-20T10:00:00Z",
            transaction_reference="DUPLICATE01",
        )
        response = self.client.post(reverse("payment-list"), {
            "invoice": self.invoice.pk,
            "amount": "100.00",
            "method": "MOBILE",
            "paid_at": "2026-11-21T10:00:00Z",
            "transaction_reference": "DUPLICATE01",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("transaction_reference", response.data)
