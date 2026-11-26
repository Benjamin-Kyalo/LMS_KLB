"""Local KEMIS-style export serializers.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.institutions.models import Institution
from apps.kemis.models import DATASET_CHOICES, FORMAT_CHOICES, KemisExport, KemisFieldMapping


class KemisExportSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """Export representation; the large payload is served by ``download``."""

    generated_by_name = serializers.CharField(
        source="generated_by.full_name", read_only=True, allow_null=True,
    )
    institution_name = serializers.CharField(
        source="institution.name", read_only=True, allow_null=True,
    )

    class Meta:
        model = KemisExport
        fields = [
            "id", "reference", "institution", "institution_name", "dataset", "format",
            "status", "filters", "record_count", "generated_by", "generated_by_name",
            "generated_at", "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "reference", "record_count", "status", "generated_by", "generated_at",
            "created_at", "updated_at",
        ]
        # The view injects/overrides the institution; clients may omit it.
        extra_kwargs = {"institution": {"required": False}}


class KemisGenerateSerializer(serializers.Serializer):
    """Validated body for the ``generate`` action."""

    dataset = serializers.ChoiceField(choices=DATASET_CHOICES)
    format = serializers.ChoiceField(choices=FORMAT_CHOICES)
    filters = serializers.JSONField(default=dict, required=False)
    # Only platform administrators may select a school explicitly; the view
    # forces every other caller onto their own institution.
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), required=False,
    )


class KemisFieldMappingSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = KemisFieldMapping
        fields = "__all__"
        read_only_fields = ["reference"]
