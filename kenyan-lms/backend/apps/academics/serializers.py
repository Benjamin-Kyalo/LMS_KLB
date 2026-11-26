"""Academic serializers."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.academics.models import SchoolEvent, TimetableEntry


class TimetableEntrySerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.full_name", read_only=True)
    school_class_name = serializers.CharField(source="school_class.name", read_only=True)
    term_name = serializers.CharField(source="term.name", read_only=True)

    class Meta:
        model = TimetableEntry
        fields = "__all__"


class SchoolEventSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = SchoolEvent
        fields = "__all__"
