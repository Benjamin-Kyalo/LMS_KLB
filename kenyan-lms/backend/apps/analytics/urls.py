"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.analytics import views

router = DefaultRouter()
router.register("snapshots", views.AnalyticsSnapshotViewSet, basename="analyticssnapshot")
router.register("rules", views.RemediationRuleViewSet, basename="remediationrule")
router.register("tasks", views.RemediationTaskViewSet, basename="remediationtask")
router.register("interventions", views.InterventionTaskViewSet, basename="interventiontask")

# Explicit routes come first so "snapshots/refresh/" is not treated as a
# router detail lookup for a snapshot whose primary key is "refresh".
urlpatterns = [
    path("dashboard/", views.dashboard, name="analytics-dashboard"),
    path("cohorts/", views.cohorts, name="analytics-cohorts"),
    path("early-warning/", views.early_warning, name="analytics-early-warning"),
    path("early-warning/refresh/", views.refresh_early_warning_endpoint, name="analytics-early-warning-refresh"),
    path("remediation/summary/", views.remediation_summary_endpoint, name="analytics-remediation-summary"),
    path("remediation/evaluate/", views.evaluate_remediation_endpoint, name="analytics-remediation-evaluate"),
    path("my-tasks/", views.my_remediation_tasks, name="analytics-my-tasks"),
    path("my-tasks/<int:pk>/complete/", views.complete_my_remediation_task, name="analytics-my-task-complete"),
    path("my-tasks/<int:pk>/dismiss/", views.dismiss_my_remediation_task, name="analytics-my-task-dismiss"),
    path("snapshots/refresh/", views.refresh_snapshot_endpoint, name="analytics-snapshots-refresh"),
    path("", include(router.urls)),
]
