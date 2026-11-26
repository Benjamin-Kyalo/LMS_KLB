"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.analytics.models import AnalyticsSnapshot, InterventionTask, RemediationRule, RemediationTask


class AnalyticsSnapshotSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source="generated_by.full_name", read_only=True)

    class Meta:
        model = AnalyticsSnapshot
        fields = "__all__"
        read_only_fields = ["institution", "reference", "generated_by", "generated_at"]


class RemediationRuleSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = RemediationRule
        fields = "__all__"
        read_only_fields = ["institution", "reference"]


class RemediationTaskSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True, allow_null=True)
    competency_name = serializers.CharField(
        source="competency.name", read_only=True, allow_null=True
    )

    class Meta:
        model = RemediationTask
        fields = "__all__"
        read_only_fields = ["institution", "reference", "resolved_at"]


class InterventionTaskSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    admission_number = serializers.CharField(source="learner.admission_number", read_only=True)
    class_name = serializers.CharField(source="learner.class_room.display_name", read_only=True, allow_null=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = InterventionTask
        fields = "__all__"
        read_only_fields = [
            "institution", "reference", "resolved_at", "risk_level", "risk_score", "signals"
        ]

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.full_name if obj.assigned_to_id else ""
