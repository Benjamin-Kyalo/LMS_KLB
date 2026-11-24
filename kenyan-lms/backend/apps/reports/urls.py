"""Report routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.reports import views

router = DefaultRouter()
router.register("snapshots", views.ReportSnapshotViewSet, basename="reportssnapshot")

urlpatterns = [
    path("dashboard/", views.school_dashboard, name="school-dashboard"),
    path("analytics/", views.analytics, name="report-analytics"),
    path("my-learners/", views.my_learners, name="report-my-learners"),
    path("learner/<int:learner_id>/", views.learner_report, name="learner-report"),
    path("", include(router.urls)),
]
