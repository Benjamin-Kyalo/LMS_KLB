"""Fee ledger routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fees.views import (
    FeeInvoiceViewSet, FeeStructureViewSet, PaymentViewSet, my_invoices,
    reconciliation_exceptions,
)

router = DefaultRouter()
router.register("structures", FeeStructureViewSet, basename="feestructure")
router.register("invoices", FeeInvoiceViewSet, basename="feeinvoice")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("my-invoices/", my_invoices, name="fee-my-invoices"),
    path("reconciliation/", reconciliation_exceptions, name="fee-reconciliation"),
    path("", include(router.urls)),
]
