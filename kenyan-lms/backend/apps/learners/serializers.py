"""Learner serializers."""
import csv
from io import StringIO
from itertools import islice

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.core.constants import Roles
from apps.learners.models import GuardianLinkRequest, Learner, LearnerGuardian, TransferRecord

User = get_user_model()


def _csv_limit(names, default):
    """Read a configurable cap from settings, with a safe built-in default."""
    for name in names:
        value = getattr(settings, name, None)
        if value is not None:
            return value
    return default


class LearnerSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="user.full_name", read_only=True)
    admission_number_value = serializers.CharField(source="admission_number", read_only=True)
    class_name = serializers.CharField(source="class_room.name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Learner
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class LearnerCreateSerializer(serializers.Serializer):
    """Creates the login account and learner record together."""

    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    # Leave blank to let the system allocate ADM-<SCHOOL>-<NNN>.
    admission_number = serializers.CharField(required=False, allow_blank=True)
    assessment_number = serializers.CharField(required=False, allow_blank=True)
    class_room = serializers.IntegerField(required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Fail with a clear message before touching the database."""
        request = self.context["request"]
        institution = request.user.institution
        if institution is None:
            raise serializers.ValidationError(
                "Platform administrators must choose an institution before adding learners."
            )
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "That username is already taken."})
        admission = attrs.get("admission_number", "").strip()
        if admission and Learner.objects.filter(
            institution=institution, admission_number=admission
        ).exists():
            raise serializers.ValidationError(
                {"admission_number": "That admission number already exists in this institution."}
            )
        assessment = attrs.get("assessment_number", "").strip()
        if assessment and Learner.objects.filter(assessment_number=assessment).exists():
            raise serializers.ValidationError(
                {"assessment_number": "That assessment number is already in use."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        # No password is invented or displayed. The account starts with an
        # unusable password; an administrator issues a password reset link.
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email", ""),
            role=Roles.LEARNER,
            institution=request.user.institution,
            must_change_password=False,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        learner = Learner.objects.create(
            user=user,
            institution=request.user.institution,
            admission_number=validated_data.get("admission_number", "").strip(),
            assessment_number=validated_data.get("assessment_number", ""),
            class_room_id=validated_data.get("class_room"),
            date_of_birth=validated_data.get("date_of_birth"),
            gender=validated_data.get("gender", ""),
        )
        return learner


class BulkImportSerializer(serializers.Serializer):
    """Accepts bounded CSV text with a header row."""

    csv_text = serializers.CharField()

    def validate_csv_text(self, value):
        max_bytes = _csv_limit(
            ("LEARNER_CSV_MAX_BYTES", "BULK_IMPORT_MAX_BYTES"), 1024 * 1024
        )
        max_rows = _csv_limit(
            ("LEARNER_CSV_MAX_ROWS", "BULK_IMPORT_MAX_ROWS"), 500
        )
        if len(value.encode("utf-8")) > max_bytes:
            raise serializers.ValidationError(
                f"CSV text is too large; the limit is {max_bytes} bytes."
            )
        reader = csv.DictReader(StringIO(value))
        required = {"username", "first_name", "last_name", "admission_number"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise serializers.ValidationError(
                "CSV must contain columns: username, first_name, last_name, admission_number"
            )
        # Stop as soon as we know the cap is exceeded; the header is not a row.
        if sum(1 for _ in islice(reader, max_rows + 1)) > max_rows:
            raise serializers.ValidationError(
                f"CSV has too many rows; the limit is {max_rows} rows "
                "(excluding the header)."
            )
        return value

    def save(self):
        reader = csv.DictReader(StringIO(self.validated_data["csv_text"]))
        created = []
        for row in reader:
            data = dict(row)
            serializer = LearnerCreateSerializer(data=data, context=self.context)
            serializer.is_valid(raise_exception=True)
            created.append(serializer.save())
        return created


class LearnerGuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerGuardian
        fields = "__all__"


class TransferRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferRecord
        fields = "__all__"


class GuardianLinkRequestSerializer(serializers.ModelSerializer):
    guardian_name = serializers.CharField(source="guardian.user.full_name", read_only=True)
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.full_name", read_only=True)

    class Meta:
        model = GuardianLinkRequest
        fields = [
            "id", "reference", "guardian", "guardian_name", "learner", "learner_name",
            "learner_identifier", "admission_number", "relationship", "status",
            "notes", "verified_link", "decided_by", "decided_by_name", "decided_at",
            "created_at",
        ]
        read_only_fields = [
            "id", "reference", "guardian_name", "learner_name", "admission_number",
            "decided_by", "decided_by_name", "decided_at", "created_at",
        ]


class GuardianLinkRequestCreateSerializer(serializers.Serializer):
    learner_identifier = serializers.CharField(max_length=50)
    relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)


class GuardianLinkDecisionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False, default=False)
