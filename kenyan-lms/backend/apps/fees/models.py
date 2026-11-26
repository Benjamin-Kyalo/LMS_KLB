"""School fee structures, invoices and payment receipts (sample/demo data).

This is a lightweight school-office ledger, not a bank or mobile-money gateway.
No payment credentials or card data are stored here.
"""
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum

from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel


class FeeStructure(AutoReferenceModelMixin, InstitutionScopedModel):
    reference = models.CharField(max_length=50, blank=True, unique=True)
    name = models.CharField(max_length=180)
    term = models.ForeignKey("institutions.Term", on_delete=models.CASCADE, related_name="fee_structures")
    school_class = models.ForeignKey(
        "institutions.SchoolClass", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="fee_structures",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("institution", "name", "term")]

    def __str__(self):
        return f"{self.name} - {self.amount}"


class FeeInvoice(AutoReferenceModelMixin, InstitutionScopedModel):
    STATUS = [
        ("PENDING", "Pending"),
        ("PARTIAL", "Partially paid"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    reference = models.CharField(max_length=50, blank=True, unique=True)
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="fee_invoices")
    fee_structure = models.ForeignKey(
        FeeStructure, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices",
    )
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-issue_date", "-id"]

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def _refresh_totals(self):
        paid = self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        self.amount_paid = paid
        if paid >= self.amount_due:
            self.status = "PAID"
        elif paid > 0:
            self.status = "PARTIAL"
        else:
            self.status = "PENDING"
        self.save(update_fields=["amount_paid", "status", "updated_at"])

    def __str__(self):
        return f"{self.reference} - {self.learner}"


class Payment(AutoReferenceModelMixin, InstitutionScopedModel):
    METHODS = [
        ("CASH", "Cash"),
        ("BANK", "Bank transfer"),
        ("MOBILE", "Mobile money"),
        ("OTHER", "Other"),
    ]

    reference = models.CharField(max_length=50, blank=True, unique=True)
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHODS, default="CASH")
    paid_at = models.DateTimeField()
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_payments",
    )
    # M-Pesa readiness: the office records the transaction code and payer
    # number after confirming the message. No API credential or PIN is stored.
    transaction_reference = models.CharField(max_length=100, blank=True, db_index=True)
    payer_phone = models.CharField(max_length=30, blank=True)
    reconciliation_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Awaiting confirmation"),
            ("RECONCILED", "Reconciled"),
            ("EXCEPTION", "Needs review"),
        ],
        default="PENDING",
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-paid_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "transaction_reference"],
                condition=models.Q(transaction_reference__gt=""),
                name="unique_payment_transaction_reference",
            )
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._refresh_invoice()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice._refresh_totals()
        return result

    def _refresh_invoice(self):
        self.invoice._refresh_totals()

    def __str__(self):
        return f"{self.reference} - {self.amount}"
