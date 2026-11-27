"""Throttles for external integration traffic."""
from apps.core.throttling import ScopedThrottle


class OneRosterThrottle(ScopedThrottle):
    """Limit by client id, not by a shared NAT or proxy IP."""

    scope = "oneroster_read"

    def get_cache_key(self, request, view):
        principal = getattr(request, "user", None)
        client_id = getattr(principal, "client_id", None)
        if not client_id:
            return None
        return self.cache_format % {"scope": self.scope, "ident": client_id}


class IntegrationUnsupportedThrottle(ScopedThrottle):
    """Limit anonymous probes of deliberately unsupported protocols."""

    scope = "integration_unsupported"
