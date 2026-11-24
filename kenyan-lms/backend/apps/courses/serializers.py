"""Course serializers."""
from rest_framework import serializers

from apps.courses.models import Assignment, Course, Lesson, LessonProgress, Module, Submission


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    module_count = serializers.IntegerField(source="modules.count", read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = ["institution"]

    def validate_code(self, value):
        value = (value or "").strip()
        request = self.context.get("request")
        institution_id = getattr(getattr(request, "user", None), "institution_id", None)
        if value and institution_id:
            queryset = Course.objects.filter(institution_id=institution_id, code=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("That course code already exists in this institution.")
        return value


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)

    class Meta:
        model = LessonProgress
        fields = "__all__"
        read_only_fields = ["institution"]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = "__all__"
        read_only_fields = ["institution", "created_by"]


class SubmissionSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = ["institution", "submitted_at", "score", "feedback", "graded_by", "graded_at"]
