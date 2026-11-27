"""Health check used by both humans and monitoring tools."""
import logging

from django.conf import settings
from django.db import connection, transaction
from rest_framework import status as http_status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes, throttle_classes,
)
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.core.audit import log_audit
from apps.core.data_quality import SAFE_FIXES, apply_fix, preview_fix, scan_institution
from apps.core.models import AuditLog, PublicEnquiry
from apps.core.permissions import IsSuperAdmin, is_institution_admin, is_platform_admin
from apps.core.serializers import (
    AuditLogSerializer, PublicEnquiryAdminSerializer, PublicEnquiryCreateSerializer,
)
from apps.core.throttling import PublicEnquiryThrottle
from apps.institutions.models import Institution

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Report whether the API and the database are reachable."""
    database_ok = True
    error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pragma: no cover - only fails when DB is down
        database_ok = False
        logger.exception("Database health probe failed")
        error = "Database unavailable"

    return Response(
        {
            "status": "ok" if database_ok else "error",
            "service": "KLB Elimu",
            "database": "connected" if database_ok else "unavailable",
            "error": error,
        },
        status=200 if database_ok else 503,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def client_config(request):
    """Public browser switches for low-bandwidth mode.

    Only booleans, path allowlists and limits are returned. No environment
    secret, session value, CSRF token or learner record is exposed here.
    """
    response = Response({
        "version": settings.OFFLINE_CONFIG_VERSION,
        "offline": {
            "enabled": settings.OFFLINE_MODE_ENABLED,
            "service_worker": False,
            "native_app": False,
            "credentials_stored": False,
            "read_cache": {
                "enabled": settings.OFFLINE_MODE_ENABLED and settings.OFFLINE_READ_CACHE_ENABLED,
                "paths": settings.OFFLINE_CACHE_PATHS,
                "max_age_seconds": settings.OFFLINE_CACHE_TTL_SECONDS,
                "max_items": settings.OFFLINE_MAX_CACHED_READS,
            },
            "outbox": {
                "enabled": settings.OFFLINE_MODE_ENABLED and settings.OFFLINE_OUTBOX_ENABLED,
                "methods": ["PATCH", "DELETE"],
                "paths": settings.OFFLINE_OUTBOX_PATHS,
                "max_items": settings.OFFLINE_OUTBOX_MAX_ITEMS,
            },
        },
    })
    response["Cache-Control"] = "public, max-age=300"
    return response


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([PublicEnquiryThrottle])
def public_enquiry_submit(request):
    """Store a public contact message and return its real reference number.

    No session, token or learner record is required. Only the contact fields
    shown on the public form are accepted, and the save plus audit entry are
    one transaction so a failed submission cannot leave a partial record.
    """
    serializer = PublicEnquiryCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        enquiry = serializer.save()
        log_audit(
            None, "public_enquiry.received", "PublicEnquiry", enquiry.reference,
            {"reference": enquiry.reference, "category": enquiry.category},
            request=request,
        )
    return Response(
        {
            "reference": enquiry.reference,
            "message": "Your enquiry has been received. Keep your reference number for any follow-up communication.",
        },
        status=http_status.HTTP_201_CREATED,
    )


class PublicEnquiryViewSet(ModelViewSet):
    """Platform-administrator review queue for public enquiries."""

    serializer_class = PublicEnquiryAdminSerializer
    permission_classes = [IsSuperAdmin]
    http_method_names = ["get", "patch", "head", "options"]
    filterset_fields = ["status", "category"]
    search_fields = ["reference", "full_name", "email", "organisation", "subject"]
    ordering_fields = ["created_at", "subject"]

    def get_queryset(self):
        return PublicEnquiry.objects.all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        enquiry = serializer.save()
        log_audit(
            self.request.user, "public_enquiry.status_changed", "PublicEnquiry",
            enquiry.reference,
            {"reference": enquiry.reference, "status": enquiry.status},
            request=self.request,
        )


class AuditLogViewSet(ReadOnlyModelViewSet):
    """Append-only audit history, visible only inside the reader's school.

    Platform super admins can review every school. Rows cannot be created,
    changed or deleted through the API: the audit trail must stay trustworthy.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["action", "entity_type", "entity_id", "user"]
    search_fields = ["action", "entity_type", "user__username"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user", "institution")
        user = self.request.user
        if is_platform_admin(user):
            return queryset
        if user.institution_id:
            return queryset.filter(institution_id=user.institution_id)
        return queryset.none()


def _data_quality_institution(user, requested_id):
    """Admins scan their own school; platform admins must name one school."""
    if not (is_platform_admin(user) or is_institution_admin(user)):
        raise PermissionDenied("Data quality tools are available to administrators only.")
    if is_platform_admin(user) and requested_id:
        try:
            return Institution.objects.get(pk=requested_id)
        except (Institution.DoesNotExist, ValueError, TypeError) as exc:
            raise ValidationError({"institution": "Choose a valid institution."}) from exc
    if user.institution_id:
        return user.institution
    raise ValidationError({"institution": "Choose an institution to scan."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def data_quality(request):
    """Read-only scan; no records are altered by a GET request."""
    institution = _data_quality_institution(request.user, request.query_params.get("institution"))
    return Response(scan_institution(institution))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def data_quality_fix(request):
    """Preview a safe fix by default; apply only with an explicit confirmation."""
    institution = _data_quality_institution(request.user, request.data.get("institution"))
    code = request.data.get("issue_type") or request.data.get("code")
    if not code:
        raise ValidationError({"issue_type": "Choose an issue to fix."})
    if code not in SAFE_FIXES:
        raise ValidationError({"issue_type": "This issue has no safe automatic fix."})
    confirmed = str(request.data.get("confirm", "")).lower() in {"1", "true", "yes"}
    if not confirmed:
        return Response(preview_fix(institution, code))
    result = apply_fix(institution, code, request.user, request)
    log_audit(
        request.user, "data_quality.fix_applied", "DataQuality", institution.pk,
        {"issue_type": code, "changes": result["change_count"]},
        institution=institution, request=request,
    )
    return Response(result)
