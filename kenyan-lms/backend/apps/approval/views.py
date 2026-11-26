"""KICD-style internal review workflow; this does not submit anything to KICD and does not represent official KICD approval."""
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.approval.models import ApprovalChecklistItem, ApprovalDecision, ApprovalRequest
from apps.approval.serializers import (
    ApprovalChecklistItemSerializer,
    ApprovalDecisionSerializer,
    ApprovalRequestSerializer,
)
from apps.core.constants import ContentStatus
from apps.core.permissions import IsContentCurator, is_content_curator, is_platform_admin
from apps.core.viewsets import (
    InstitutionScopedQuerysetMixin,
    StaffWriteMixin,
)


def _can_curate(user):
    """Content curators and platform admins may review and publish."""
    return is_content_curator(user) or is_platform_admin(user)


class ApprovalRequestViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.select_related(
        "institution", "submitted_by", "reviewed_by", "textbook", "content_resource",
    ).prefetch_related("checklist", "decisions")
    serializer_class = ApprovalRequestSerializer
    filterset_fields = ["status", "content_type", "textbook", "submitted_by", "reviewed_by"]
    search_fields = ["reference", "title", "summary", "kicd_reference"]

    def get_permissions(self):
        if self.action == "summary":
            return [IsAuthenticated()]
        if self.action in {"review", "publish"}:
            # IsContentCurator also admits platform administrators (see
            # apps.core.permissions.is_content_curator).
            return [IsAuthenticated(), IsContentCurator()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        approval_request = self.get_object()
        if approval_request.status not in ApprovalRequest.SUBMITTABLE_STATUSES:
            return Response(
                {"detail": "Only draft, rejected or returned requests can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if approval_request.checklist.filter(is_met=False).exists():
            return Response(
                {"detail": "All checklist items must be met before submission."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        approval_request.status = "SUBMITTED"
        approval_request.submitted_by = request.user
        approval_request.submitted_at = timezone.now()
        approval_request.save(update_fields=[
            "status", "submitted_by", "submitted_at", "updated_at",
        ])
        return Response(self.get_serializer(approval_request).data)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        if not _can_curate(request.user):
            raise PermissionDenied("Only content curators or platform administrators may review requests.")
        approval_request = self.get_object()
        if approval_request.status not in ApprovalRequest.REVIEWABLE_STATUSES:
            return Response(
                {"detail": "Only submitted or under-review requests can be reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision_value = request.data.get("decision")
        if not isinstance(decision_value, str) or decision_value not in ApprovalDecision.RESULTING_STATUS:
            return Response(
                {"detail": "Choose a valid decision: APPROVE, REJECT or REQUEST_CHANGES."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        notes = str(request.data.get("notes", "") or "")

        with transaction.atomic():
            ApprovalDecision.objects.create(
                institution=approval_request.institution,
                request=approval_request,
                decision=decision_value,
                notes=notes,
                decided_by=request.user,
                reference_to_source=str(request.data.get("reference_to_source", "") or "")[:200],
            )
            approval_request.status = ApprovalDecision.RESULTING_STATUS[decision_value]
            approval_request.reviewed_by = request.user
            approval_request.reviewed_at = timezone.now()
            approval_request.review_notes = notes
            approval_request.save(update_fields=[
                "status", "reviewed_by", "reviewed_at", "review_notes", "updated_at",
            ])
        return Response(self.get_serializer(approval_request).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        if not _can_curate(request.user):
            raise PermissionDenied("Only content curators or platform administrators may publish requests.")
        approval_request = self.get_object()
        if approval_request.status != "APPROVED":
            return Response(
                {"detail": "Only approved requests can be published."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            textbook = approval_request.textbook
            if textbook is not None:
                textbook.status = ContentStatus.PUBLISHED
                textbook.save(update_fields=["status", "updated_at"])
            approval_request.status = "PUBLISHED"
            approval_request.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(approval_request).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Counts by status for the caller's institution scope."""
        queryset = self.get_queryset()
        counts = {
            value: queryset.filter(status=value).count()
            for value, _label in ApprovalRequest.STATUS_CHOICES
        }
        return Response({
            "total": queryset.count(),
            "by_status": counts,
            **counts,
        })


class ApprovalDecisionViewSet(InstitutionScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """Decisions are created by the review action, not by a separate write endpoint."""

    queryset = ApprovalDecision.objects.select_related("request", "decided_by")
    serializer_class = ApprovalDecisionSerializer
    filterset_fields = ["request", "decision", "decided_by"]
    search_fields = ["reference", "notes", "reference_to_source", "request__title"]


class ApprovalChecklistItemViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ApprovalChecklistItem.objects.select_related("request")
    serializer_class = ApprovalChecklistItemSerializer
    filterset_fields = ["request", "is_met"]
    search_fields = ["reference", "label", "notes"]
