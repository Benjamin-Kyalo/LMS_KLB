"""Shared serializer mixins and read models."""
from rest_framework import serializers

from apps.core.models import AuditLog


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