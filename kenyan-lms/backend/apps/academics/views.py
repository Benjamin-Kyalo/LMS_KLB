"""Academic API endpoints."""
from rest_framework import viewsets

from apps.academics.models import SchoolEvent, TimetableEntry
from apps.academics.serializers import SchoolEventSerializer, TimetableEntrySerializer
from apps.core.constants import Capabilities
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin, StaffWriteMixin


class TimetableEntryViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = TimetableEntry.objects.select_related("subject", "teacher__user")
    serializer_class = TimetableEntrySerializer
    filterset_fields = ["school_class", "term", "day_of_week"]


class SchoolEventViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    capability = Capabilities.ACADEMICS_MANAGE
    queryset = SchoolEvent.objects.all()
    serializer_class = SchoolEventSerializer
    filterset_fields = ["event_type", "is_published"]
    search_fields = ["title", "description"]
