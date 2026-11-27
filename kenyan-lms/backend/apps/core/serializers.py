"""Shared serializer mixins and read models."""
from rest_framework import serializers

from apps.core.models import AuditLog, PublicEnquiry


class InstitutionCodeMixin:
    """Expose the owning institution's code on institution-scoped records."""

    institution_code = serializers.SerializerMethodField()

    def get_institution_code(self, obj):
        institution = getattr(obj, "institution", None)
        if institution is None:
            return ""
        return getattr(institution, "code", "") or ""


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_username = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = [
            "id", "institution", "user", "action", "entity_type", "entity_id",
            "details", "ip_address", "created_at",
        ]

    def get_actor_name(self, obj):
        return getattr(obj.user, "full_name", "") if obj.user_id else ""

    def get_actor_username(self, obj):
        return getattr(obj.user, "username", "") if obj.user_id else ""


class PublicEnquiryCreateSerializer(serializers.ModelSerializer):
    """Validate a public contact message without trusting client metadata."""

    class Meta:
        model = PublicEnquiry
        fields = [
            "id", "reference", "full_name", "email", "phone", "organisation",
            "category", "subject", "message", "status", "created_at",
        ]
        read_only_fields = ["id", "reference", "status", "created_at"]

    def validate(self, attrs):
        cleaned = {}
        for key, value in attrs.items():
            if isinstance(value, str):
                value = " ".join(value.split())
            cleaned[key] = value
        for key in ("full_name", "category", "subject", "message"):
            if not cleaned.get(key):
                raise serializers.ValidationError(
                    {key: "Complete this field before sending your enquiry."}
                )
        return cleaned


class PublicEnquiryAdminSerializer(serializers.ModelSerializer):
    """Platform review view: only the workflow status can be changed."""

    class Meta:
        model = PublicEnquiry
        fields = "__all__"
        read_only_fields = [
            "id", "reference", "full_name", "email", "phone", "organisation",
            "category", "subject", "message", "created_at", "updated_at",
        ]