"""Small shared helpers for writing audit records.

Audit rows are append-only. Call this from state-changing views after the
database transaction has succeeded, or inside it when the action itself is
atomic.
"""
import json

from django.core.serializers.json import DjangoJSONEncoder

from apps.core.models import AuditLog

SENSITIVE_FIELDS = {"password", "secret", "token", "api_key", "password_hash"}


def _jsonable(value):
    """Convert a model/date/decimal value into safe JSON for audit details."""
    if hasattr(value, "pk") and not isinstance(value, (str, int, float, bool)):
        return value.pk
    return value


def _json_safe(data):
    """Coerce dates, decimals and model references into JSON-safe values."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder, default=str))


def snapshot(instance, extra=None):
    """Return a JSON-safe before/after snapshot of a model instance."""
    data = {}
    for field in instance._meta.fields:
        if field.name in SENSITIVE_FIELDS:
            continue
        value = getattr(instance, field.attname if field.is_relation else field.name)
        data[field.name] = _jsonable(value)
    for key, value in (extra or {}).items():
        if key not in SENSITIVE_FIELDS:
            data[key] = _jsonable(value)
    return _json_safe(data)


def record_change(user, instance, before, after, action=None, request=None, institution=None):
    """Append one field-level diff when a sensitive record actually changed."""
    before = _json_safe(before)
    after = _json_safe(after)
    changed = sorted(
        key for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    )
    if not changed:
        return None
    entity_type = type(instance).__name__
    return log_audit(
        user,
        action or f"{entity_type.lower()}.updated",
        entity_type,
        getattr(instance, "pk", None),
        {
            "changed_fields": changed,
            "before": {key: before.get(key) for key in changed},
            "after": {key: after.get(key) for key in changed},
        },
        institution=institution or getattr(instance, "institution_id", None),
        request=request,
    )


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
