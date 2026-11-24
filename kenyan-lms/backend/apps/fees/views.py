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

from apps.core.constants import Roles
from apps.core.concurrency import ConflictAwareMixin
from apps.core.permissions import same_institution
from apps.core.viewsets import (
    AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin,
)
from apps.fees.models import FeeInvoice, FeeStructure, Payment
from apps.fees.serializers import (
    FeeInvoiceSerializer, FeeStructureSerializer, PaymentSerializer,
)
from apps.learners.models import LearnerGuardian
from apps.reports.scoping import scoped_institution_id


class FeeStructureViewSet(
    ConflictAwareMixin, AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    queryset = FeeStructure.objects.select_related("term", "school_class")
    serializer_class = FeeStructureSerializer
    filterset_fields = ["term", "school_class", "is_active"]
    search_fields = ["name", "reference"]
    ordering_fields = ["name", "amount", "due_date", "created_at"]


class FeeInvoiceViewSet(
    ConflictAwareMixin, StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    queryset = FeeInvoice.objects.select_related("learner__user", "fee_structure")
    serializer_class = FeeInvoiceSerializer
    filterset_fields = ["learner", "status", "fee_structure"]
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
    queryset = Payment.objects.select_related("invoice", "recorded_by")
    serializer_class = PaymentSerializer
    filterset_fields = ["invoice", "method", "recorded_by"]
    search_fields = ["reference", "notes", "invoice__reference"]
    ordering_fields = ["paid_at", "amount"]

    def perform_create(self, serializer):
        invoice = serializer.validated_data.get("invoice")
        if invoice and not same_institution(self.request.user, invoice.institution_id):
            raise PermissionDenied("You cannot record a payment for another school's invoice.")
        self._scoped_save(
            serializer,
            recorded_by=self.request.user if self.request.user.is_authenticated else None,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_invoices(request):
    """Invoices for the signed-in learner, or for a guardian's linked learners.

    A guardian link must explicitly grant ``can_view_fees``. This endpoint does
    not expose school-wide invoices to families.
    """
    user = request.user
    if user.role == Roles.LEARNER:
        invoices = FeeInvoice.objects.filter(learner__user=user)
    elif user.role == Roles.GUARDIAN:
        learner_ids = LearnerGuardian.objects.filter(
            guardian__user=user, can_view_fees=True
        ).values_list("learner_id", flat=True)
        invoices = FeeInvoice.objects.filter(learner_id__in=learner_ids)
    elif user.role in Roles.STAFF_ROLES:
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
