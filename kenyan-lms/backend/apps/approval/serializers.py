"""KICD-style internal review workflow; this does not submit anything to KICD and does not represent official KICD approval."""
from rest_framework import serializers

from apps.approval.models import ApprovalChecklistItem, ApprovalDecision, ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source="submitted_by.full_name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.full_name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    textbook_title = serializers.CharField(source="textbook.title", read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = "__all__"
        read_only_fields = ["reference", "institution"]


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    request_title = serializers.CharField(source="request.title", read_only=True)
    request_reference = serializers.CharField(source="request.reference", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.full_name", read_only=True)

    class Meta:
        model = ApprovalDecision
        fields = "__all__"
        read_only_fields = ["reference", "institution", "decided_at"]


class ApprovalChecklistItemSerializer(serializers.ModelSerializer):
    request_title = serializers.CharField(source="request.title", read_only=True)
    request_reference = serializers.CharField(source="request.reference", read_only=True)

    class Meta:
        model = ApprovalChecklistItem
        fields = "__all__"
        read_only_fields = ["reference", "institution"]
