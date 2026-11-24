"""Teacher API endpoints."""
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin
from apps.teachers.models import LessonPlan, Teacher, TeacherClassAssignment
from apps.teachers.serializers import (
    LessonPlanSerializer, TeacherClassAssignmentSerializer, TeacherCreateSerializer, TeacherSerializer,
)


class TeacherViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
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


class TeacherClassAssignmentViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TeacherClassAssignment.objects.all()
    serializer_class = TeacherClassAssignmentSerializer
    filterset_fields = ["teacher", "school_class", "subject", "academic_year"]


class LessonPlanViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = LessonPlan.objects.all()
    serializer_class = LessonPlanSerializer
    filterset_fields = ["teacher", "school_class", "subject", "status"]
    search_fields = ["title", "objectives"]
