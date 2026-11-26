"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.engine import (
    build_cohorts,
    dashboard_metrics,
    evaluate_remediation as evaluate_rules,
    refresh_snapshot as build_snapshot,
    remediation_summary,
)
from apps.analytics.early_warning import build_early_warning, refresh_early_warning
from apps.analytics.models import (
    AnalyticsSnapshot, InterventionTask, RemediationRule, RemediationTask,
)
from apps.analytics.serializers import (
    AnalyticsSnapshotSerializer,
    InterventionTaskSerializer,
    RemediationRuleSerializer,
    RemediationTaskSerializer,
)
from apps.core.constants import Capabilities, Roles
from apps.core.permissions import IsInstitutionAdmin, IsStaff
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.learners.models import Learner
from apps.learners.scoping import FamilyScopedReadMixin
from apps.reports.scoping import dashboard_viewer


def _scope_institution(user):
    """Fail closed for users who are not attached to one school."""
    if not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")
    if not user.institution_id:
        raise PermissionDenied("This endpoint needs a user linked to an institution.")
    return user.institution


def _scope_staff_institution(user):
    if not dashboard_viewer(user):
        raise PermissionDenied("This summary is available to school staff only.")
    return _scope_institution(user)


def _own_learner(user):
    """Learner record belonging to the signed-in learner, never a guessed id."""
    if not user.is_authenticated or user.role != Roles.LEARNER:
        raise PermissionDenied("This view is available to learners only.")
    institution = _scope_institution(user)
    learner = Learner.objects.filter(user=user, institution=institution).first()
    if learner is None:
        raise PermissionDenied("Your learner record is not available.")
    return learner


def _own_task(user, pk):
    learner = _own_learner(user)
    task = RemediationTask.objects.filter(pk=pk, learner=learner).first()
    if task is None:
        raise Http404("That support task is not available.")
    return task


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_remediation_tasks(request):
    """Support tasks for the signed-in learner only."""
    learner = _own_learner(request.user)
    tasks = RemediationTask.objects.filter(
        institution=learner.institution, learner=learner
    ).select_related("learner", "rule", "competency", "assigned_to")
    return Response(RemediationTaskSerializer(tasks, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_my_remediation_task(request, pk):
    task = _own_task(request.user, pk)
    task.status = RemediationTask.COMPLETED
    task.resolved_at = timezone.now()
    task.save(update_fields=["status", "resolved_at", "updated_at"])
    return Response(RemediationTaskSerializer(task, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dismiss_my_remediation_task(request, pk):
    task = _own_task(request.user, pk)
    task.status = RemediationTask.DISMISSED
    task.resolved_at = timezone.now()
    task.save(update_fields=["status", "resolved_at", "updated_at"])
    return Response(RemediationTaskSerializer(task, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Scoped aggregate KPIs computed from existing school records."""
    return Response(dashboard_metrics(_scope_staff_institution(request.user)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cohorts(request):
    """Class/subject cohorts built from live learner, attendance and result rows."""
    institution = _scope_staff_institution(request.user)
    return Response(build_cohorts(institution, request.query_params.dict()))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def remediation_summary_endpoint(request):
    """Current remediation task counts by status."""
    return Response(remediation_summary(_scope_staff_institution(request.user)))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStaff])
def evaluate_remediation_endpoint(request):
    """Run the active rules for the caller's institution."""
    return Response(evaluate_rules(_scope_institution(request.user)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def early_warning(request):
    """Rule-based learner risk flags with the evidence behind each flag."""
    institution = _scope_staff_institution(request.user)
    return Response(build_early_warning(institution, request.query_params.dict()))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStaff])
def refresh_early_warning_endpoint(request):
    """Recalculate flags and raise intervention tasks for medium/high risk."""
    institution = _scope_institution(request.user)
    return Response(refresh_early_warning(institution, request.user, request))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstitutionAdmin])
def refresh_snapshot_endpoint(request):
    """Recompute and store one snapshot for an institution and period."""
    institution = _scope_institution(request.user)
    dataset = request.data.get("dataset")
    period = request.data.get("period")
    if not dataset or not period:
        raise ValidationError({"dataset": "Dataset and period are required."})
    try:
        snapshot = build_snapshot(institution, dataset, period, request.user)
    except ValueError as exc:
        raise ValidationError({"dataset": str(exc)}) from exc
    return Response(
        AnalyticsSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED
    )


class AnalyticsSnapshotViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = AnalyticsSnapshot.objects.select_related("generated_by")
    serializer_class = AnalyticsSnapshotSerializer
    filterset_fields = ["dataset", "period", "generated_by"]
    search_fields = ["reference", "period"]


class RemediationRuleViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RemediationRule.objects.select_related("competency", "target_course", "target_resource")
    serializer_class = RemediationRuleSerializer
    filterset_fields = ["is_active", "action", "competency", "mastery_below"]
    search_fields = ["reference", "name", "notes"]

    @action(detail=True, methods=["patch"], url_path="toggle")
    def toggle(self, request, pk=None):
        """Enable or disable a rule without replacing its configuration."""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        return Response(self.get_serializer(rule).data)


class RemediationTaskViewSet(
    FamilyScopedReadMixin, StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    queryset = RemediationTask.objects.select_related(
        "learner", "rule", "competency", "assigned_to"
    )
    serializer_class = RemediationTaskSerializer
    filterset_fields = ["status", "learner", "rule", "competency", "assigned_to", "due_date"]
    search_fields = ["reference"]
    # Support tasks are academic records: verified guardians only see tasks
    # for children whose link grants academic access.
    learner_path = "learner"
    guardian_permission = "can_view_academics"

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        """Assign a task to a user from the same institution."""
        task = self.get_object()
        user_id = request.data.get("user_id")
        User = get_user_model()
        try:
            assignee = User.objects.get(pk=user_id)
        except (User.DoesNotExist, DjangoValidationError, ValueError, TypeError) as exc:
            raise ValidationError({"user_id": "Choose a valid user."}) from exc
        if assignee.institution_id != task.institution_id:
            raise ValidationError({"user_id": "Choose a user from this institution."})
        task.assigned_to = assignee
        task.status = RemediationTask.ASSIGNED
        task.save()
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """Mark a task completed and record when it was resolved."""
        task = self.get_object()
        task.status = RemediationTask.COMPLETED
        task.resolved_at = timezone.now()
        task.save()
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        """Dismiss a task without counting it as completed."""
        task = self.get_object()
        task.status = RemediationTask.DISMISSED
        task.resolved_at = timezone.now()
        task.save()
        return Response(self.get_serializer(task).data)


class InterventionTaskViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.REPORTS_VIEW
    queryset = InterventionTask.objects.select_related(
        "learner__user", "learner__class_room", "assigned_to"
    )
    serializer_class = InterventionTaskSerializer
    filterset_fields = ["status", "risk_level", "learner", "assigned_to"]
    search_fields = ["reference", "notes"]

    def _same_institution_user(self, request, task):
        user_id = request.data.get("user_id")
        User = get_user_model()
        try:
            assignee = User.objects.get(pk=user_id)
        except (User.DoesNotExist, DjangoValidationError, ValueError, TypeError) as exc:
            raise ValidationError({"user_id": "Choose a valid user."}) from exc
        if assignee.institution_id != task.institution_id:
            raise ValidationError({"user_id": "Choose a user from this institution."})
        return assignee

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        task = self.get_object()
        task.assigned_to = self._same_institution_user(request, task)
        task.status = InterventionTask.ASSIGNED
        task.save(update_fields=["assigned_to", "status", "updated_at"])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = InterventionTask.COMPLETED
        task.resolved_at = timezone.now()
        task.save(update_fields=["status", "resolved_at", "updated_at"])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        task = self.get_object()
        task.status = InterventionTask.DISMISSED
        task.resolved_at = timezone.now()
        task.save(update_fields=["status", "resolved_at", "updated_at"])
        return Response(self.get_serializer(task).data)
