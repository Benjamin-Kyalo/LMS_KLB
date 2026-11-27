"""Scope checks for OneRoster read endpoints."""
from rest_framework.permissions import BasePermission

from apps.integration.clients import OneRosterPrincipal


class HasOneRosterScope(BasePermission):
    """Require the scope named on the view for the authenticated client."""

    message = "This client is not permitted to read that resource."

    def has_permission(self, request, view):
        principal = getattr(request, "user", None)
        required = getattr(view, "oneroster_scope", "")
        return (
            isinstance(principal, OneRosterPrincipal)
            and bool(required)
            and required in principal.scopes
        )
