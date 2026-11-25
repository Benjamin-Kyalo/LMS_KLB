"""Teacher serializers."""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import OnboardingProfile
from apps.core.constants import Roles
from apps.teachers.models import LessonPlan, Teacher, TeacherApproval, TeacherClassAssignment

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
        teacher = Teacher.objects.create(
            user=user,
            institution=request.user.institution,
            staff_number=validated_data.get("staff_number", "").strip(),
            phone=validated_data.get("phone", ""),
        )
        TeacherApproval.objects.create(
            institution=request.user.institution,
            teacher=teacher,
            status="APPROVED",
            decided_by=request.user,
            decided_at=timezone.now(),
            notes="Created directly by an administrator.",
        )
        profile, _ = OnboardingProfile.objects.get_or_create(user=user)
        profile.teacher_approved = True
        profile.mark_complete_if_ready()
        profile.save(update_fields=["teacher_approved", "completed_at", "updated_at"])
        return teacher


class TeacherClassAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassAssignment
        fields = "__all__"


class LessonPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPlan
        fields = "__all__"


class TeacherApprovalSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.full_name", read_only=True)
    email = serializers.EmailField(source="teacher.user.email", read_only=True)
    staff_number = serializers.CharField(source="teacher.staff_number", read_only=True)
    employment_type = serializers.CharField(source="teacher.employment_type", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.full_name", read_only=True)
    assignment_ids = serializers.SerializerMethodField()

    class Meta:
        model = TeacherApproval
        fields = [
            "id", "reference", "teacher", "teacher_name", "email", "staff_number",
            "employment_type", "status", "notes", "decided_by", "decided_by_name",
            "decided_at", "created_at", "assignment_ids",
        ]
        read_only_fields = [
            "id", "reference", "teacher_name", "email", "staff_number",
            "employment_type", "decided_by", "decided_by_name", "decided_at",
            "created_at", "assignment_ids",
        ]

    def get_assignment_ids(self, obj):
        return list(obj.teacher.assignments.values_list("id", flat=True))


class TeacherApprovalActionSerializer(serializers.Serializer):
    """Optional assignment data accepted when approving a teacher."""

    notes = serializers.CharField(required=False, allow_blank=True)
    school_class = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.IntegerField(required=False, allow_null=True)
    academic_year = serializers.IntegerField(required=False, allow_null=True)
    is_class_teacher = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        assignment_fields = ["school_class", "subject", "academic_year"]
        supplied = [field for field in assignment_fields if attrs.get(field)]
        if supplied and len(supplied) != len(assignment_fields):
            raise serializers.ValidationError({
                field: "All class, subject and academic year are required for an assignment."
                for field in assignment_fields
            })
        return attrs
