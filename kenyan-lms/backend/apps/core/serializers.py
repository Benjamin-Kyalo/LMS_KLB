"""Shared serializer mixins."""
from rest_framework import serializers


class InstitutionCodeMixin:
    """Expose the owning institution's code on institution-scoped records."""

    institution_code = serializers.SerializerMethodField()

    def get_institution_code(self, obj):
        institution = getattr(obj, "institution", None)
        if institution is None:
            return ""
        return getattr(institution, "code", "") or ""