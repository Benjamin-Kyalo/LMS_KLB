"""Attendance serializers."""
from rest_framework import serializers

from apps.attendance.models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = "__all__"
        read_only_fields = ["marked_by", "marked_at"]
        # The view injects the signed-in user's institution after validation.
        extra_kwargs = {"institution": {"required": False}}


class BulkAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    school_class = serializers.IntegerField()
    term = serializers.IntegerField(required=False, allow_null=True)
    records = serializers.ListField(child=serializers.DictField())

    def validate_records(self, value):
        for item in value:
            if "learner" not in item or "status" not in item:
                raise serializers.ValidationError("Each record needs 'learner' and 'status'.")
        return value
