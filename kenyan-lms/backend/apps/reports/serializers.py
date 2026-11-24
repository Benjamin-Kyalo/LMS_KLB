"""Report serializers."""
from rest_framework import serializers

from apps.reports.models import ReportSnapshot


class ReportSnapshotSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source="generated_by.full_name", read_only=True)

    class Meta:
        model = ReportSnapshot
        fields = "__all__"
        read_only_fields = ["institution", "generated_by"]
