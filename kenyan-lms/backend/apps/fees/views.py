"""Fee ledger endpoints.

This is a school-office ledger. It records locally issued invoices and the
payments a school office has recorded against them. There is no payment
gateway, no card data and no mobile-money credential in this app.
"""
from django.db.models import Count, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.audit import log_audit
from apps.core.constants import Capabilities, Roles
from apps.core.concurrency import ConflictAwareMixin
from apps.core.permissions import has_capability, is_staff_user, same_institution
from apps.core.viewsets import (
    AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin,
)
from apps.communications.services import notify_users
from apps.fees.models import FeeInvoice, FeeStructure, Payment
from apps.learners.models import LearnerGuardian
from apps.fees.serializers import (
    FeeInvoiceSerializer, FeeStructureSerializer, PaymentSerializer,
)
from apps.learners.scoping import FamilyScopedReadMixin, visible_learner_ids
from apps.reports.scoping import scoped_institution_id


class FeeStructureViewSet(
    ConflictAwareMixin, AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    capability = Capabilities.FEES_MANAGE
    queryset = FeeStructure.objects.select_related("term", "school_class")
    serializer_class = FeeStructureSerializer
    filterset_fields = ["term", "school_class", "is_active"]
    search_fields = ["name", "reference"]
    ordering_fields = ["name", "amount", "due_date", "created_at"]


class FeeInvoiceViewSet(
    FamilyScopedReadMixin, ConflictAwareMixin, StaffWriteMixin,
    InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    capability = Capabilities.FEES_MANAGE
    queryset = FeeInvoice.objects.select_related("learner__user", "fee_structure")
    serializer_class = FeeInvoiceSerializer
    filterset_fields = ["learner", "status", "fee_structure"]
    # Same family rule as the my-invoices portal endpoint: a verified link
    # must explicitly grant can_view_fees.
    learner_path = "learner"
    guardian_permission = "can_view_fees"
    search_fields = ["reference", "learner__user__first_name", "learner__user__last_name"]
    ordering_fields = ["issue_date", "due_date", "amount_due", "status"]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Totals for the current scope, never another school's money."""
        queryset = self.filter_queryset(self.get_queryset())
        totals = queryset.aggregate(
            invoices=Count("id"),
            due=Sum("amount_due"),
            paid=Sum("amount_paid"),
        )
        due = totals["due"] or 0
        paid = totals["paid"] or 0
        by_status = list(
            queryset.values("status").annotate(count=Count("id"), total=Sum("amount_due"))
        )
        return Response({
            "invoices": totals["invoices"] or 0,
            "amount_due": due,
            "amount_paid": paid,
            "balance": due - paid,
            "by_status": by_status,
        })


class PaymentViewSet(
    ConflictAwareMixin, StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    capability = Capabilities.FEES_MANAGE
    queryset = Payment.objects.select_related(
        "invoice__institution", "invoice__learner__user", "recorded_by"
    )
    serializer_class = PaymentSerializer
    filterset_fields = ["invoice", "method", "recorded_by", "reconciliation_status"]
    search_fields = ["reference", "notes", "invoice__reference", "transaction_reference"]
    ordering_fields = ["paid_at", "amount"]

    def perform_create(self, serializer):
        invoice = serializer.validated_data.get("invoice")
        if invoice and not same_institution(self.request.user, invoice.institution_id):
            raise PermissionDenied("You cannot record a payment for another school's invoice.")
        method = serializer.validated_data.get("method", "CASH")
        code = (serializer.validated_data.get("transaction_reference") or "").strip()
        if method == "MOBILE":
            status_value = "PENDING" if code else "EXCEPTION"
        else:
            status_value = "RECONCILED"
            serializer.validated_data["transaction_reference"] = ""
            serializer.validated_data["payer_phone"] = ""
        self._scoped_save(
            serializer,
            recorded_by=self.request.user if self.request.user.is_authenticated else None,
            transaction_reference=code,
            reconciliation_status=status_value,
        )
        log_audit(
            self.request.user, "payment.recorded", "Payment", serializer.instance.pk,
            {
                "invoice": serializer.instance.invoice_id,
                "amount": str(serializer.instance.amount),
                "method": method,
                "reconciliation_status": status_value,
            },
            institution=serializer.instance.institution_id,
            request=self.request,
        )
        notify_users(
            [
                link.guardian.user for link in LearnerGuardian.objects.filter(
                    learner=invoice.learner, is_verified=True, can_view_fees=True
                ).select_related("guardian__user")
            ],
            "A fee payment was recorded",
            f"{serializer.instance.amount} was recorded for {invoice.learner.user.full_name}.",
            "SYSTEM",
            "/portal/fees",
        )

    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Printable receipt data derived from a recorded payment."""
        payment = self.get_object()
        invoice = payment.invoice
        institution = invoice.institution
        return Response({
            "receipt_number": payment.reference,
            "issued_at": payment.created_at,
            "paid_at": payment.paid_at,
            "school_name": institution.name if institution else "",
            "school_code": institution.code if institution else "",
            "learner_name": invoice.learner.user.full_name,
            "admission_number": invoice.learner.admission_number,
            "invoice_reference": invoice.reference,
            "fee_name": invoice.fee_structure.name if invoice.fee_structure_id else "",
            "amount": payment.amount,
            "method": payment.get_method_display(),
            "transaction_reference": payment.transaction_reference,
            "payer_phone": payment.payer_phone,
            "recorded_by_name": payment.recorded_by.full_name if payment.recorded_by_id else "",
            "reconciliation_status": payment.get_reconciliation_status_display(),
        })

    @action(detail=True, methods=["post"], url_path="reconcile")
    def reconcile(self, request, pk=None):
        """Confirm a recorded mobile-money payment after checking the message."""
        payment = self.get_object()
        code = str(request.data.get("transaction_reference") or payment.transaction_reference or "").strip()
        if payment.method == "MOBILE" and not code:
            raise ValidationError({
                "transaction_reference": "Enter the M-Pesa transaction code before reconciling."
            })
        duplicate = Payment.objects.filter(
            institution=payment.institution_id, transaction_reference=code
        ).exclude(pk=payment.pk)
        if code and duplicate.exists():
            raise ValidationError({
                "transaction_reference": "This transaction code is already recorded for this school."
            })
        payment.transaction_reference = code
        payment.reconciliation_status = "RECONCILED"
        payment.notes = str(request.data.get("notes") or payment.notes or "")
        payment.save(
            update_fields=["transaction_reference", "reconciliation_status", "notes", "updated_at"]
        )
        log_audit(
            request.user, "payment.reconciled", "Payment", payment.pk,
            {
                "transaction_reference": code,
                "reconciliation_status": "RECONCILED",
            },
            institution=payment.institution_id, request=request,
        )
        return Response(self.get_serializer(payment).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reconciliation_exceptions(request):
    """Payments that need office review, scoped to the caller's school."""
    user = request.user
    if not (is_staff_user(user) or has_capability(user, Capabilities.FEES_MANAGE)):
        raise PermissionDenied("Fee reconciliation is available to school staff only.")
    if not user.institution_id and not (user.is_super_admin or user.is_platform_user):
        return Response({"exceptions": [], "counts": {"missing_reference": 0, "flagged": 0, "duplicates": 0}})
    payments = Payment.objects.select_related("invoice__learner__user", "recorded_by")
    institution_id = scoped_institution_id(user)
    if institution_id is not None:
        payments = payments.filter(institution_id=institution_id)
    duplicates = set(
        row["transaction_reference"]
        for row in payments.exclude(transaction_reference="")
        .values("transaction_reference")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    missing = payments.filter(method="MOBILE", transaction_reference="")
    flagged = payments.filter(reconciliation_status="EXCEPTION")
    duplicate_rows = payments.filter(transaction_reference__in=duplicates) if duplicates else payments.none()
    items = []
    for payment, reason in (
        *((item, "MISSING_TRANSACTION_REFERENCE") for item in missing),
        *((item, "FLAGGED_FOR_REVIEW") for item in flagged),
        *((item, "DUPLICATE_TRANSACTION_REFERENCE") for item in duplicate_rows),
    ):
        items.append({
            "payment_id": payment.pk,
            "reference": payment.reference,
            "invoice_reference": payment.invoice.reference,
            "learner_name": payment.invoice.learner.user.full_name,
            "amount": payment.amount,
            "method": payment.get_method_display(),
            "transaction_reference": payment.transaction_reference,
            "reason": reason,
            "paid_at": payment.paid_at,
        })
    seen = set()
    unique_items = []
    for item in items:
        key = (item["payment_id"], item["reason"])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    return Response({
        "exceptions": unique_items,
        "counts": {
            "missing_reference": missing.count(),
            "flagged": flagged.count(),
            "duplicates": len(duplicates),
        },
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_invoices(request):
    """Invoices for the signed-in learner, or for a guardian's linked learners.

    A verified guardian link must explicitly grant ``can_view_fees``. This
    endpoint shares its family scoping helper with the invoice ViewSet and
    never exposes school-wide invoices to families.
    """
    user = request.user
    if user.role == Roles.LEARNER:
        invoices = FeeInvoice.objects.filter(learner__user=user)
    elif user.role == Roles.GUARDIAN:
        invoices = FeeInvoice.objects.filter(
            learner_id__in=visible_learner_ids(user, "can_view_fees")
        )
    elif is_staff_user(user) or has_capability(user, Capabilities.FEES_MANAGE):
        learner_id = request.query_params.get("learner")
        if not learner_id:
            raise ValidationError({"learner": "A learner id is required for staff views."})
        invoices = FeeInvoice.objects.filter(learner_id=learner_id)
        if scoped_institution_id(user) is not None:
            invoices = invoices.filter(institution_id=scoped_institution_id(user))
    else:
        return Response(
            {"detail": "Your role cannot view fee records."}, status=status.HTTP_403_FORBIDDEN
        )

    invoices = invoices.select_related("learner__user", "fee_structure").order_by("-issue_date", "-id")
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(invoices, request)
    serializer = FeeInvoiceSerializer(page if page is not None else invoices, many=True)
    if page is not None:
        return paginator.get_paginated_response(serializer.data)
    return Response(serializer.data)
