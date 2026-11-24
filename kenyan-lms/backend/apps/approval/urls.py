"""KICD-style internal review workflow; this does not submit anything to KICD and does not represent official KICD approval."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.approval import views

router = DefaultRouter()
router.register("requests", views.ApprovalRequestViewSet, basename="approvalrequest")
router.register("decisions", views.ApprovalDecisionViewSet, basename="approvaldecision")
router.register("checklist", views.ApprovalChecklistItemViewSet, basename="approvalchecklistitem")

urlpatterns = [path("", include(router.urls))]
