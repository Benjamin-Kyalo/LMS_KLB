"""Learner routes (corrected ordering)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.learners import views

router = DefaultRouter()
router.register("guardian-links", views.LearnerGuardianViewSet, basename="learnerguardian")
router.register("transfers", views.TransferRecordViewSet, basename="transferrecord")
router.register("", views.LearnerViewSet, basename="learner")

urlpatterns = [path("", include(router.urls))]
