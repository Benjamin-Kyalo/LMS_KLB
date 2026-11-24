"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from rest_framework import serializers

from apps.analytics.models import AnalyticsSnapshot, RemediationRule, RemediationTask


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source="generated_by.full_name", read_only=True)

    class Meta:
        model = AnalyticsSnapshot
        fields = "__all__"
        read_only_fields = ["institution", "reference", "generated_by", "generated_at"]


class RemediationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemediationRule
        fields = "__all__"
        read_only_fields = ["institution", "reference"]


class RemediationTaskSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True, allow_null=True)
    competency_name = serializers.CharField(
        source="competency.name", read_only=True, allow_null=True
    )

    class Meta:
        model = RemediationTask
        fields = "__all__"
        read_only_fields = ["institution", "reference", "resolved_at"]
