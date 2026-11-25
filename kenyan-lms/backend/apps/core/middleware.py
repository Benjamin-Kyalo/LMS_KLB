"""Small, dependency-free hardening middleware.

Django's SecurityMiddleware and CsrfViewMiddleware already provide the core
transport protections. This middleware adds the remaining browser policies and
makes sure authenticated API responses are never stored by shared caches.
"""
from django.conf import settings


class SecurityHeadersMiddleware:
    """Apply configured response headers and a strict no-store API policy."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        for header, value in getattr(settings, "SECURITY_HEADERS", {}).items():
            if value and header not in response:
                response[header] = value

        user = getattr(request, "user", None)
        if (
            request.path.startswith("/api/")
            and user is not None
            and getattr(user, "is_authenticated", False)
            and "Cache-Control" not in response
        ):
            response["Cache-Control"] = "no-store"

        return response
