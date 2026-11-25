"""Teacher API endpoints."""
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import OnboardingProfile
from apps.core.audit import log_audit
from apps.core.constants import Capabilities
from apps.core.permissions import capability_permission
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.teachers.models import LessonPlan, Teacher, TeacherApproval, TeacherClassAssignment
from apps.teachers.serializers import (
    LessonPlanSerializer, TeacherApprovalActionSerializer, TeacherApprovalSerializer,
    TeacherClassAssignmentSerializer, TeacherCreateSerializer, TeacherSerializer,
)


class TeacherViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.TEACHERS_MANAGE
    search_fields = ["user__first_name", "user__last_name", "staff_number"]
    filterset_fields = ["is_active", "employment_type", "institution"]

    def get_queryset(self):
        return super().get_queryset().select_related("user", "institution").prefetch_related("subjects")

    def get_serializer_class(self):
        if self.action == "create":
            return TeacherCreateSerializer
        return TeacherSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        output = TeacherSerializer(teacher, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class TeacherApprovalViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Admin-only review queue for teachers who registered publicly."""

    capability = Capabilities.TEACHERS_MANAGE
    serializer_class = TeacherApprovalSerializer
    filterset_fields = ["status"]
    # Approval decisions are made only through the explicit actions below.
    http_method_names = ["get", "post", "head", "options"]
    search_fields = ["teacher__user__first_name", "teacher__user__last_name", "teacher__staff_number"]

    def get_permissions(self):
        return [
            IsAuthenticated(),
            capability_permission(Capabilities.TEACHERS_MANAGE)(),
        ]

    def get_queryset(self):
        return super().get_queryset().select_related(
            "teacher__user", "decided_by", "institution"
        ).prefetch_related("teacher__assignments")

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        approval = self.get_object()
        if approval.status != "PENDING":
            raise ValidationError("Only pending teacher approvals can be approved.")

        payload = TeacherApprovalActionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        teacher = approval.teacher
        teacher.is_active = True
        teacher.save(update_fields=["is_active"])
        user = teacher.user
        user.is_active = True
        user.save(update_fields=["is_active"])

        if data.get("school_class") and data.get("subject") and data.get("academic_year"):
            TeacherClassAssignment.objects.get_or_create(
                institution=approval.institution,
                teacher=teacher,
                school_class_id=data["school_class"],
                subject_id=data["subject"],
                academic_year_id=data["academic_year"],
                defaults={"is_class_teacher": data.get("is_class_teacher", False)},
            )

        profile, _ = OnboardingProfile.objects.get_or_create(user=user)
        profile.teacher_approved = True
        if TeacherClassAssignment.objects.filter(teacher=teacher).exists():
            profile.classes_assigned = True
        profile.mark_complete_if_ready()
        profile.save(update_fields=[
            "teacher_approved", "classes_assigned", "completed_at", "updated_at"
        ])

        approval.status = "APPROVED"
        approval.notes = data.get("notes", "")
        approval.decided_by = request.user
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "notes", "decided_by", "decided_at", "updated_at"])

        log_audit(
            request.user, "approve", "TeacherApproval", approval.pk,
            {"teacher": teacher.pk, "reference": approval.reference},
            institution=approval.institution, request=request,
        )
        return Response(TeacherApprovalSerializer(approval).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        approval = self.get_object()
        if approval.status != "PENDING":
            raise ValidationError("Only pending teacher approvals can be rejected.")
        notes = (request.data.get("notes") or "").strip()
        if not notes:
            raise ValidationError({"notes": "Give a short reason for rejecting this account."})

        approval.status = "REJECTED"
        approval.notes = notes
        approval.decided_by = request.user
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "notes", "decided_by", "decided_at", "updated_at"])

        log_audit(
            request.user, "reject", "TeacherApproval", approval.pk,
            {"teacher": approval.teacher_id, "reference": approval.reference},
            institution=approval.institution, request=request,
        )
        return Response(TeacherApprovalSerializer(approval).data)


class TeacherClassAssignmentViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.TEACHERS_MANAGE
    queryset = TeacherClassAssignment.objects.all()
    serializer_class = TeacherClassAssignmentSerializer
    filterset_fields = ["teacher", "school_class", "subject", "academic_year"]


class LessonPlanViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.TEACHERS_MANAGE
    queryset = LessonPlan.objects.all()
    serializer_class = LessonPlanSerializer
    filterset_fields = ["teacher", "school_class", "subject", "status"]
    search_fields = ["title", "objectives"]
