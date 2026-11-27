"""Course serializers."""
from decimal import Decimal

from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.core.permissions import is_staff_user as core_is_staff_user, same_institution
from apps.curriculum.models import RubricCriterion
from apps.courses.models import (
    Assignment, Course, Lesson, LessonProgress, Module, Submission,
    SubmissionAttempt, SubmissionCriterionScore,
)
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


class LessonSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class ModuleSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = "__all__"


class CourseSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
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


class LessonProgressSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
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


class AssignmentSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    rubric_name = serializers.CharField(source="rubric.name", read_only=True)

    class Meta:
        model = Assignment
        fields = "__all__"
        read_only_fields = ["institution", "created_by"]

    def validate_max_attempts(self, value):
        if value < 1:
            raise serializers.ValidationError("Allow at least one attempt.")
        return value

    def validate_rubric(self, value):
        request = self.context.get("request")
        if value and request:
            user = request.user
            if value.institution_id is not None and not same_institution(user, value.institution_id):
                raise serializers.ValidationError("That rubric belongs to another institution.")
        return value


class SubmissionAttemptSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = SubmissionAttempt
        fields = "__all__"
        read_only_fields = [
            "institution", "submission", "attempt_number", "submitted_at",
            "score", "feedback", "graded_at",
        ]


class SubmissionCriterionScoreSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = SubmissionCriterionScore
        fields = "__all__"
        read_only_fields = [
            "institution", "submission", "attempt_number", "criterion_name",
            "max_score", "score", "comment",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = getattr(self.context.get("request"), "user", None)
        if user and not is_staff_user(user) and not instance.submission.feedback_published_at:
            data.pop("score", None)
            data.pop("comment", None)
        return data


class SubmissionSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    attempts = SubmissionAttemptSerializer(many=True, read_only=True)
    criterion_scores = serializers.SerializerMethodField()
    rubric = serializers.PrimaryKeyRelatedField(source="assignment.rubric", read_only=True)
    rubric_name = serializers.CharField(source="assignment.rubric.name", read_only=True)
    achievement_level = serializers.CharField(source="rubric_level.name", read_only=True)
    assignment_max_score = serializers.DecimalField(
        source="assignment.max_score", read_only=True, max_digits=6, decimal_places=2,
    )
    allow_resubmission = serializers.BooleanField(source="assignment.allow_resubmission", read_only=True)
    max_attempts = serializers.IntegerField(source="assignment.max_attempts", read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = [
            "institution", "submitted_at", "score", "feedback", "graded_by", "graded_at",
            "rubric_level", "rubric_level_name", "rubric_max_score", "private_notes",
            "feedback_published_at", "current_attempt",
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

    def get_criterion_scores(self, obj):
        rows = obj.criterion_scores.filter(
            attempt_number=obj.current_attempt
        ).select_related("criterion")
        return SubmissionCriterionScoreSerializer(
            rows, many=True, context=self.context
        ).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = getattr(self.context.get("request"), "user", None)
        if user and not is_staff_user(user):
            data.pop("private_notes", None)
            if not instance.feedback_published_at:
                for key in (
                    "score", "feedback", "graded_by", "graded_at",
                    "rubric_level", "rubric_level_name", "rubric_max_score", "rubric_name",
                    "achievement_level",
                ):
                    data.pop(key, None)
        return data


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


class RubricCriterionMarkSerializer(serializers.Serializer):
    """One row of the staff marking grid; the criterion is validated server-side."""

    criterion = serializers.PrimaryKeyRelatedField(queryset=RubricCriterion.objects.all())
    score = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class GradeWithRubricSerializer(serializers.Serializer):
    """Strict payload for criterion-based grading."""

    criteria = RubricCriterionMarkSerializer(many=True)
    overall_feedback = serializers.CharField(required=False, allow_blank=True, default="")
    private_notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_criteria(self, value):
        if not value:
            raise serializers.ValidationError("Score at least one criterion.")
        submission = self.context["submission"]
        rubric = submission.assignment.rubric
        if rubric is None:
            raise serializers.ValidationError("This assignment does not use a rubric.")
        ids = [row["criterion"].pk for row in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("A criterion may only be scored once.")
        allowed = set(rubric.criteria.values_list("pk", flat=True))
        for row in value:
            criterion = row["criterion"]
            if criterion.pk not in allowed:
                raise serializers.ValidationError(
                    f"'{criterion.name}' is not part of this assignment's rubric."
                )
            institution_id = criterion.rubric.institution_id
            if institution_id is not None and not same_institution(
                self.context.get("request").user if self.context.get("request") else None,
                institution_id,
            ):
                raise serializers.ValidationError("That criterion belongs to another institution.")
            if row["score"] > criterion.max_score:
                raise serializers.ValidationError(
                    f"'{criterion.name}' cannot exceed {criterion.max_score}."
                )
        return value

    def validate(self, attrs):
        submission = self.context["submission"]
        total = sum((row["score"] for row in attrs["criteria"]), Decimal("0"))
        max_score = submission.assignment.max_score
        if total > max_score:
            raise serializers.ValidationError({
                "criteria": f"The total cannot exceed the assignment maximum of {max_score}."
            })
        attrs["total_score"] = total
        return attrs


class ResubmitSerializer(serializers.Serializer):
    """A new attempt must contain answer text or an uploaded file."""

    text_answer = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate(self, attrs):
        if not (attrs.get("text_answer") or "").strip() and not attrs.get("attachment"):
            raise serializers.ValidationError({
                "text_answer": "Add an answer or attach a file before resubmitting."
            })
        submission = self.context["submission"]
        assignment = submission.assignment
        if not assignment.allow_resubmission:
            raise serializers.ValidationError("This assignment does not allow resubmission.")
        if submission.current_attempt >= assignment.max_attempts:
            raise serializers.ValidationError("No attempts remain for this assignment.")
        return attrs


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
