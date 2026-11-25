"""Course serializers."""
from rest_framework import serializers

from apps.core.permissions import is_staff_user as core_is_staff_user, same_institution
from apps.courses.models import Assignment, Course, Lesson, LessonProgress, Module, Submission
from apps.learners.models import Learner


SAFE_SUBMISSION_STATUSES = {"DRAFT", "SUBMITTED"}


def is_staff_user(user):
    """Same staff rule as IsStaff, including custom roles with capabilities."""
    return core_is_staff_user(user)


def _check_related_institution(user, obj, label):
    if not same_institution(user, obj.institution_id):
        raise serializers.ValidationError(f"The {label} belongs to another institution.")


def _check_own_learner(user, learner):
    if is_staff_user(user):
        return
    own = getattr(user, "learner_profile", None)
    if own is None or own.pk != learner.pk:
        raise serializers.ValidationError("You may only record work for yourself.")


class CurrentLearnerDefault:
    """Fill the learner from the request so unique-together checks see it."""

    requires_context = True

    def __call__(self, serializer_field):
        request = serializer_field.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or is_staff_user(user):
            return None
        return getattr(user, "learner_profile", None)


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
        read_only_fields = ["institution", "status", "completed_at", "synced_at"]
        # Non-staff learner is derived server-side; staff must supply one.
        extra_kwargs = {
            "learner": {
                "required": False,
                "allow_null": True,
                "default": CurrentLearnerDefault(),
            },
        }

    def validate_lesson(self, value):
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "lesson")
        return value

    def validate_learner(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "learner")
            _check_own_learner(request.user, value)
        return value


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
        read_only_fields = [
            "institution", "submitted_at", "score", "feedback", "graded_by", "graded_at",
        ]
        # Non-staff learner is derived server-side; staff must supply one.
        extra_kwargs = {
            "learner": {
                "required": False,
                "allow_null": True,
                "default": CurrentLearnerDefault(),
            },
        }

    def validate_status(self, value):
        # Graded/returned states are set by the server, only via `grade`.
        if value not in SAFE_SUBMISSION_STATUSES:
            raise serializers.ValidationError("Only draft/submitted status can be set here.")
        return value

    def validate_assignment(self, value):
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "assignment")
        return value

    def validate_learner(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "learner")
            _check_own_learner(request.user, value)
        return value


class GradeSubmissionSerializer(serializers.Serializer):
    """Validated payload for the staff-only grade action."""

    score = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_score(self, value):
        submission = self.context["submission"]
        max_score = submission.assignment.max_score
        if value > max_score:
            raise serializers.ValidationError(
                f"Score cannot exceed the assignment maximum of {max_score}."
            )
        return value


class MarkLessonCompleteSerializer(serializers.Serializer):
    """Resolve IDs to in-scope objects before a progress write."""

    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    learner = serializers.PrimaryKeyRelatedField(queryset=Learner.objects.all(), required=False)

    def validate_lesson(self, value):
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "lesson")
        return value

    def validate_learner(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "learner")
            _check_own_learner(request.user, value)
        return value
