"""Local KEMIS-style export endpoints.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
import csv
import io
import json

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status as response_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import is_platform_admin
from apps.core.viewsets import InstitutionScopedQuerysetMixin, PlatformWriteMixin, StaffWriteMixin
from apps.kemis.builders import DATASET_LABELS, build_rows, default_columns
from apps.kemis.models import KemisExport, KemisFieldMapping
from apps.kemis.serializers import (
    KemisExportSerializer,
    KemisFieldMappingSerializer,
    KemisGenerateSerializer,
)


def _render_csv(headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def _render_json(headers, rows, dataset, institution):
    return json.dumps(
        {
            "dataset": dataset,
            "institution": {
                "id": institution.pk,
                "code": institution.code,
                "name": institution.name,
            },
            "columns": headers,
            "record_count": len(rows),
            "records": rows,
        },
        ensure_ascii=False,
        indent=2,
    )


class KemisExportViewSet(StaffWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Staged exports, scoped to the caller's institution."""

    queryset = KemisExport.objects.select_related("generated_by", "institution")
    serializer_class = KemisExportSerializer
    filterset_fields = ["dataset", "format", "status"]
    search_fields = ["reference", "notes"]

    def get_permissions(self):
        # Column metadata is harmless reference data; the other custom
        # actions follow StaffWriteMixin (generate/download are staff-only).
        if self.action == "datasets":
            return [IsAuthenticated()]
        return super().get_permissions()

    def _target_institution(self, validated_data):
        user = self.request.user
        if is_platform_admin(user):
            institution = validated_data.get("institution") or user.institution
        else:
            # Never trust a client-supplied school for ordinary staff.
            institution = user.institution
        if institution is None:
            raise ValidationError(
                {"institution": "Choose an institution before generating an export."}
            )
        return institution

    def perform_create(self, serializer):
        user = self.request.user
        if not is_platform_admin(user) and not user.institution_id:
            raise ValidationError({"institution": "A KEMIS export needs an institution."})
        if (
            is_platform_admin(user) and not user.institution_id
            and not self.request.data.get("institution")
        ):
            raise ValidationError({"institution": "Choose an institution for this export."})
        super().perform_create(serializer)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        body = KemisGenerateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        dataset = body.validated_data["dataset"]
        export_format = body.validated_data["format"]
        filters = body.validated_data.get("filters") or {}
        institution = self._target_institution(body.validated_data)

        try:
            headers, rows = build_rows(dataset, institution, filters=filters)
            if export_format == "CSV":
                content = _render_csv(headers, rows)
            else:
                content = _render_json(headers, rows, dataset, institution)
        except Exception:
            # Keep the failure record for review without exposing internals.
            KemisExport.objects.create(
                institution=institution,
                dataset=dataset,
                format=export_format,
                filters=filters,
                status="FAILED",
                generated_by=request.user,
                generated_at=timezone.now(),
                notes="Generation failed. Check the filters and try again.",
            )
            raise ValidationError("The export could not be generated. Check the filters and try again.")

        export = KemisExport.objects.create(
            institution=institution,
            dataset=dataset,
            format=export_format,
            filters=filters,
            status="READY",
            record_count=len(rows),
            generated_by=request.user,
            generated_at=timezone.now(),
            payload=content,
        )
        data = KemisExportSerializer(export, context={"request": request}).data
        return Response(
            {
                **data,
                "payload": export.payload,
                "preview": rows[:5],
                "preview_columns": headers,
            },
            status=response_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        export = self.get_object()
        if export.format == "CSV":
            response = HttpResponse(export.payload, content_type="text/csv; charset=utf-8")
            extension = "csv"
        else:
            response = HttpResponse(export.payload, content_type="application/json; charset=utf-8")
            extension = "json"
        filename = f"kemis-{export.reference or export.pk}.{extension}"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=["get"])
    def datasets(self, request):
        mapped = {}
        for item in KemisFieldMapping.objects.filter(is_active=True).order_by("dataset", "ordering"):
            mapped.setdefault(item.dataset, []).append(
                {
                    "source_field": item.source_field,
                    "target_column": item.target_column,
                    "is_required": item.is_required,
                }
            )
        return Response(
            [
                {
                    "dataset": key,
                    "label": label,
                    "default_columns": default_columns(key),
                    "mapped_columns": mapped.get(key, []),
                }
                for key, label in DATASET_LABELS.items()
            ]
        )


class KemisFieldMappingViewSet(PlatformWriteMixin, viewsets.ModelViewSet):
    """Platform-managed local column mappings (writes: platform admins only)."""

    queryset = KemisFieldMapping.objects.all()
    serializer_class = KemisFieldMappingSerializer
    filterset_fields = ["dataset", "is_active", "is_required"]
    search_fields = ["source_field", "target_column", "reference", "notes"]
