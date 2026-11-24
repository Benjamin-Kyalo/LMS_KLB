"""Learner serializers."""
import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.core.constants import Roles
from apps.learners.models import Learner, LearnerGuardian, TransferRecord

User = get_user_model()


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
    """Accepts CSV text with a header row."""

    csv_text = serializers.CharField()

    def validate_csv_text(self, value):
        reader = csv.DictReader(StringIO(value))
        required = {"username", "first_name", "last_name", "admission_number"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise serializers.ValidationError(
                "CSV must contain columns: username, first_name, last_name, admission_number"
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
