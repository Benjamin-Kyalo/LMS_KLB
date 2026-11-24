"""Teacher serializers."""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.core.constants import Roles
from apps.teachers.models import LessonPlan, Teacher, TeacherClassAssignment

User = get_user_model()


class TeacherSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    subject_names = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = "__all__"

    def get_subject_names(self, obj):
        return list(obj.subjects.values_list("name", flat=True))


class TeacherCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    staff_number = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context["request"]
        staff_number = attrs.get("staff_number", "").strip()
        if staff_number and request.user.institution_id:
            if Teacher.objects.filter(
                institution=request.user.institution, staff_number=staff_number
            ).exists():
                raise serializers.ValidationError(
                    {"staff_number": "That staff number already exists in this institution."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        # No password is invented or displayed; use the password reset flow.
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email", ""),
            role=Roles.TEACHER,
            institution=request.user.institution,
            must_change_password=False,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        return Teacher.objects.create(
            user=user,
            institution=request.user.institution,
            staff_number=validated_data.get("staff_number", "").strip(),
            phone=validated_data.get("phone", ""),
        )


class TeacherClassAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassAssignment
        fields = "__all__"


class LessonPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPlan
        fields = "__all__"
