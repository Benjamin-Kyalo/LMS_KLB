"""Serializers for institution structure."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.institutions.models import (
    AcademicYear, Department, Institution, InstitutionType, SchoolClass, Subject, Term,
)


class InstitutionTypeSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = InstitutionType
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class InstitutionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
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


class InstitutionProfileSerializer(InstitutionSerializer):
    """Allowlisted fields a school admin may change through ``mine`` PATCH.

    Identity and platform-controlled fields (code, institution_type,
    is_active, settings, reference, timestamps) are not accepted here. The
    full ``InstitutionSerializer`` remains in use for platform-admin updates.
    """

    class Meta(InstitutionSerializer.Meta):
        fields = [
            "id", "name", "institution_type_name", "email", "phone", "website",
            "motto", "logo", "address_line", "town", "county", "sub_county",
            "postal_code",
        ]
        read_only_fields = ["id", "institution_type_name"]
        extra_kwargs = {}


class DepartmentSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        extra_kwargs = {"code": {"required": False, "allow_blank": True}}


class PublicInstitutionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    institution_type_name = serializers.CharField(source="institution_type.name", read_only=True)

    class Meta:
        model = Institution
        fields = ["id", "name", "code", "institution_type_name", "county", "town"]
        read_only_fields = fields


class AcademicYearSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"


class TermSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = Term
        fields = "__all__"


class SchoolClassSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class_name = serializers.CharField(source="name", read_only=True)
    display_name = serializers.CharField(read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)
    class_teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = "__all__"

    def get_class_teacher_name(self, obj):
        assignment = obj.teacher_assignments.filter(is_class_teacher=True).select_related("teacher__user").first()
        return assignment.teacher.user.full_name if assignment else None


class SubjectSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
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
