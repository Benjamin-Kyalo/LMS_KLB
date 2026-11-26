"""Shared audit and data-quality routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core import views

router = DefaultRouter()
router.register("audit", views.AuditLogViewSet, basename="auditlog")

urlpatterns = [
    path("data-quality/", views.data_quality, name="core-data-quality"),
    path("data-quality/fix/", views.data_quality_fix, name="core-data-quality-fix"),
    path("", include(router.urls)),
]
