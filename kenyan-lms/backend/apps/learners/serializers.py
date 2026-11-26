"""Learner serializers."""
import csv
import re
from io import StringIO
from itertools import islice

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.core.audit import record_change, snapshot
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.core.constants import Roles
from apps.learners.models import GuardianLinkRequest, Learner, LearnerGuardian, TransferRecord

User = get_user_model()


def _generate_username(first_name, last_name):
    base = f"{first_name}_{last_name}".strip("_").lower().replace(" ", "_")
    base = re.sub(r"[^a-z0-9_.-]", "", base)
    base = re.sub(r"_+", "_", base).strip("_.-")
    if not base:
        base = "user"
    candidate = base
    counter = 2
    while User.objects.filter(username__iexact=candidate).exists():
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def _csv_limit(names, default):
    """Read a configurable cap from settings, with a safe built-in default."""
    for name in names:
        value = getattr(settings, name, None)
        if value is not None:
            return value
    return default


class LearnerSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="user.full_name", read_only=True)
    admission_number_value = serializers.CharField(source="admission_number", read_only=True)
    class_name = serializers.CharField(source="class_room.display_name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_code = serializers.CharField(source="institution.code", read_only=True)
    guardian_names = serializers.SerializerMethodField()
    guardian_ids = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")

    def get_guardian_names(self, obj):
        return [link.guardian.user.full_name for link in obj.guardian_links.select_related("guardian__user").all()]

    def get_guardian_ids(self, obj):
        return [link.guardian_id for link in obj.guardian_links.all()]

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = instance.user
        identity_fields = ("username", "first_name", "last_name", "email")
        before = snapshot(instance, {field: getattr(user, field) for field in identity_fields})
        user_data = validated_data.pop("user", {})
        for field in identity_fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        if user_data:
            user.save()
        updated = super().update(instance, validated_data)
        after = snapshot(instance, {field: getattr(user, field) for field in identity_fields})
        record_change(
            getattr(request, "user", None), instance, before, after,
            action="learner.updated", request=request,
        )
        return updated

    class Meta:
        model = Learner
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class LearnerCreateSerializer(serializers.Serializer):
    """Creates the login account and learner record together."""

    username = serializers.CharField(required=False, allow_blank=True)
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
        username = (attrs.get("username") or "").strip()
        if username and User.objects.filter(username=username).exists():
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
        username = (validated_data.get("username") or "").strip()
        if not username:
            username = _generate_username(
                validated_data.get("first_name", ""),
                validated_data.get("last_name", ""),
            )
        user = User.objects.create_user(
            username=username,
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

    @transaction.atomic
    def save(self):
        reader = csv.DictReader(StringIO(self.validated_data["csv_text"]))
        created = []
        for row in reader:
            data = dict(row)
            serializer = LearnerCreateSerializer(data=data, context=self.context)
            serializer.is_valid(raise_exception=True)
            created.append(serializer.save())
        return created


class LearnerGuardianSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = LearnerGuardian
        fields = "__all__"
        # Our validate() supplies a clearer duplicate message than DRF's
        # generated UniqueTogetherValidator, and also checks school matching.
        validators = []

    def validate(self, attrs):
        """Stop duplicate or cross-school links before they reach the database."""
        learner = attrs.get("learner") or (self.instance.learner if self.instance else None)
        guardian = attrs.get("guardian") or (self.instance.guardian if self.instance else None)
        if learner and guardian:
            duplicate = LearnerGuardian.objects.filter(learner=learner, guardian=guardian)
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError(
                    "This guardian is already linked to this learner. No change was made."
                )
            if guardian.institution_id != learner.institution_id:
                raise serializers.ValidationError(
                    "The guardian and learner must belong to the same school."
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        link = super().create(validated_data)
        self._enforce_single_primary(link)
        return link

    @transaction.atomic
    def update(self, instance, validated_data):
        link = super().update(instance, validated_data)
        self._enforce_single_primary(link)
        return link

    @staticmethod
    def _enforce_single_primary(link):
        if link.is_primary:
            LearnerGuardian.objects.filter(learner=link.learner).exclude(pk=link.pk).update(
                is_primary=False
            )


class TransferRecordSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = TransferRecord
        fields = "__all__"


class GuardianLinkRequestSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    guardian_name = serializers.CharField(source="guardian.user.full_name", read_only=True)
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    guardian_number = serializers.CharField(source="guardian.guardian_number", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.full_name", read_only=True)

    class Meta:
        model = GuardianLinkRequest
        fields = [
            "id", "reference", "guardian", "guardian_name", "guardian_number",
            "learner", "learner_name", "learner_identifier", "admission_number",
            "relationship", "status", "notes", "verified_link", "decided_by",
            "decided_by_name", "decided_at", "created_at",
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
    # Omitted flags keep an existing link's current permissions; new links take
    # the model defaults (academics and attendance on, fees off).
    can_view_academics = serializers.BooleanField(required=False)
    can_view_attendance = serializers.BooleanField(required=False)
    can_view_fees = serializers.BooleanField(required=False)
