"""Small scoped DRF throttles for abuse-prone endpoints.

Rates live in ``settings.DEFAULT_THROTTLE_RATES`` so operators can tune them
without code changes. A multi-worker deployment should back Django's cache
with a shared store; the local default is per-process only.
"""
from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class ScopedThrottle(SimpleRateThrottle):
    """Rate-limit by authenticated user, falling back to client IP."""

    scope = ""

    def get_rate(self):
        """Read our top-level settings so overrides apply without a reload."""
        rates = getattr(settings, "DEFAULT_THROTTLE_RATES", {})
        if self.scope in rates:
            return rates[self.scope]
        return super().get_rate()

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginThrottle(ScopedThrottle):
    scope = "auth_login"


class RegistrationThrottle(ScopedThrottle):
    scope = "auth_register"


class PasswordResetThrottle(ScopedThrottle):
    scope = "auth_reset"


class TutorThrottle(ScopedThrottle):
    scope = "tutor_ask"


class ExportThrottle(ScopedThrottle):
    scope = "export_generate"
