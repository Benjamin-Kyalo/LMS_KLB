"""Guardian API endpoints."""
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.core.constants import Capabilities
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin
from apps.guardians.models import Guardian
from apps.guardians.serializers import GuardianCreateSerializer, GuardianSerializer


class GuardianViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.GUARDIANS_MANAGE
    search_fields = ["user__first_name", "user__last_name", "phone"]

    def get_queryset(self):
        return super().get_queryset().select_related("user", "institution")

    def get_serializer_class(self):
        if self.action == "create":
            return GuardianCreateSerializer
        return GuardianSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        guardian = serializer.save()
        output = GuardianSerializer(guardian, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)
