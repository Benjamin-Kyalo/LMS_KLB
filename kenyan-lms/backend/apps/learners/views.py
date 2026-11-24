"""Learner API endpoints, including safe CSV import."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin
from apps.learners.models import Learner, LearnerGuardian, TransferRecord
from apps.learners.serializers import (
    BulkImportSerializer, LearnerCreateSerializer, LearnerGuardianSerializer,
    LearnerSerializer, TransferRecordSerializer,
)


class LearnerViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Learner.objects.all()
    serializer_class = LearnerSerializer
    filterset_fields = ["institution", "class_room", "status", "gender"]
    search_fields = ["user__first_name", "user__last_name", "admission_number", "assessment_number"]

    def get_queryset(self):
        return super().get_queryset().select_related("user", "class_room", "institution")

    def get_serializer_class(self):
        if self.action == "create":
            return LearnerCreateSerializer
        return LearnerSerializer

    def create(self, request, *args, **kwargs):
        """Return the created learner using the read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        learner = serializer.save()
        output = LearnerSerializer(learner, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        serializer = BulkImportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        learners = serializer.save()
        return Response({"imported": len(learners)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def guardians(self, request, pk=None):
        learner = self.get_object()
        links = LearnerGuardian.objects.filter(learner=learner).select_related("guardian__user")
        return Response(LearnerGuardianSerializer(links, many=True).data)


class LearnerGuardianViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """
    LearnerGuardian has no institution field, so the mixin cannot filter it.
    We override get_queryset to scope through the learner instead.
    """

    serializer_class = LearnerGuardianSerializer

    def get_queryset(self):
        from apps.core.permissions import is_platform_admin
        qs = LearnerGuardian.objects.select_related("learner", "guardian__user")
        if is_platform_admin(self.request.user):
            return qs
        if self.request.user.institution_id:
            return qs.filter(learner__institution_id=self.request.user.institution_id)
        return qs.none()


class TransferRecordViewSet(AdminWriteMixin, viewsets.ModelViewSet):
    serializer_class = TransferRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TransferRecord.objects.select_related("learner__user")
        if self.request.user.is_platform_user:
            return qs
        if self.request.user.institution_id:
            return qs.filter(learner__institution_id=self.request.user.institution_id)
        return qs.none()
