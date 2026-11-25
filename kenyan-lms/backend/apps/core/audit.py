"""Small shared helper for writing audit records.

Audit rows are append-only. Call this from state-changing views after the
database transaction has succeeded, or inside it when the action itself is
atomic.
"""
from apps.core.models import AuditLog


def log_audit(user, action, entity_type, entity_id=None, details=None, institution=None, request=None):
    """Create one AuditLog row and return it.

    ``institution`` is taken from the actor when not supplied. ``request`` is
    optional and only used to capture the client IP.
    """
    resolved_institution = institution
    if resolved_institution is None:
        resolved_institution = getattr(user, "institution_id", None)
    # Callers may hold either an Institution instance or a raw primary key.
    # AuditLog.institution is an id field, so normalise models before saving.
    if resolved_institution is not None and hasattr(resolved_institution, "pk"):
        resolved_institution = resolved_institution.pk

    ip_address = None
    if request is not None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip_address = (forwarded.split(",")[0].strip() if forwarded
                      else request.META.get("REMOTE_ADDR"))

    return AuditLog.objects.create(
        institution_id=resolved_institution,
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else "",
        details=details or {},
        ip_address=ip_address,
    )
