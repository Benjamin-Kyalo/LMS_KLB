"""Serializers for institution structure."""
from rest_framework import serializers

from apps.institutions.models import (
    AcademicYear, Department, Institution, InstitutionType, SchoolClass, Subject, Term,
)


class InstitutionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionType
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class InstitutionSerializer(serializers.ModelSerializer):
    institution_type_name = serializers.CharField(source="institution_type.name", read_only=True)
    user_count = serializers.IntegerField(source="users.count", read_only=True)

    class Meta:
        model = Institution
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}

    def validate_logo(self, value):
        """Reject oversized or non-image uploads before saving them."""
        if not value:
            return value
        allowed = {"image/jpeg", "image/png", "image/webp"}
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in allowed:
            raise serializers.ValidationError("Use a JPG, PNG or WebP logo.")
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Logo must be 2 MB or smaller.")
        return value


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class PublicInstitutionSerializer(serializers.ModelSerializer):
    institution_type_name = serializers.CharField(source="institution_type.name", read_only=True)

    class Meta:
        model = Institution
        fields = ["id", "name", "code", "institution_type_name", "county", "town"]
        read_only_fields = fields


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"


class TermSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = Term
        fields = "__all__"


class SchoolClassSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    class_teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = "__all__"

    def get_class_teacher_name(self, obj):
        assignment = obj.teacher_assignments.filter(is_class_teacher=True).select_related("teacher__user").first()
        return assignment.teacher.user.full_name if assignment else None


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"

    def validate_code(self, value):
        value = (value or "").strip()
        request = self.context.get("request")
        institution_id = getattr(getattr(request, "user", None), "institution_id", None)
        if value and institution_id:
            queryset = Subject.objects.filter(institution_id=institution_id, code=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("That subject code already exists in this institution.")
        return value
