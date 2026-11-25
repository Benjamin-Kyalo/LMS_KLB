"""Institution API endpoints."""
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.constants import Capabilities
from apps.core.permissions import IsInstitutionAdmin, IsPlatformAdmin, is_institution_admin, is_platform_admin
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin, PlatformWriteMixin
from apps.institutions.models import (
    AcademicYear, Department, Institution, InstitutionType, SchoolClass, Subject, Term,
)
from apps.institutions.serializers import (
    AcademicYearSerializer, DepartmentSerializer, InstitutionProfileSerializer,
    InstitutionSerializer, InstitutionTypeSerializer, PublicInstitutionSerializer,
    SchoolClassSerializer, SubjectSerializer, TermSerializer,
)


class InstitutionTypeViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    queryset = InstitutionType.objects.all()
    serializer_class = InstitutionTypeSerializer
    permission_classes = [IsAuthenticated]


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    Platform admins see all institutions. Everyone else sees only their own.
    Only platform admins may create or delete an institution.
    """

    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Institution.objects.select_related("institution_type")
        if is_platform_admin(user):
            return queryset
        if user.institution_id:
            return queryset.filter(id=user.institution_id)
        return queryset.none()

    def get_permissions(self):
        if self.action == "mine" and self.request.method == "GET":
            return [IsAuthenticated()]
        if self.action == "mine" and self.request.method == "PATCH":
            return [IsAuthenticated(), IsInstitutionAdmin()]
        if self.action in {"create", "destroy", "update", "partial_update"}:
            return [IsAuthenticated(), IsPlatformAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get", "patch"], url_path="mine")
    def mine(self, request):
        """Let a school update its own profile without touching other schools."""
        if not request.user.institution_id:
            return Response({"detail": "This account has no institution assigned."}, status=400)
        if request.method == "PATCH" and not (is_platform_admin(request.user) or is_institution_admin(request.user)):
            return Response({"detail": "Only school administrators may edit the school profile."}, status=403)
        institution = get_object_or_404(self.get_queryset(), pk=request.user.institution_id)
        if request.method == "PATCH":
            # School admins may only edit profile fields. Platform admins keep
            # the full serializer here as well as on the detail endpoints.
            serializer_class = (
                self.get_serializer_class()
                if is_platform_admin(request.user) else InstitutionProfileSerializer
            )
            serializer = serializer_class(institution, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(institution).data)


class PublicInstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Active institutions for role-based public registration only."""

    queryset = Institution.objects.filter(is_active=True).select_related("institution_type")
    serializer_class = PublicInstitutionSerializer
    permission_classes = [AllowAny]


class DepartmentViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "code"]


class AcademicYearViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    filterset_fields = ["is_current", "institution"]


class TermViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = Term.objects.select_related("academic_year")
    serializer_class = TermSerializer
    filterset_fields = ["academic_year", "is_current"]


class SchoolClassViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = SchoolClass.objects.select_related("academic_year")
    serializer_class = SchoolClassSerializer
    filterset_fields = ["academic_year", "level", "stream"]
    search_fields = ["name", "level"]


class SubjectViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filterset_fields = ["is_active", "learning_area"]
    search_fields = ["name", "code"]
