"""Reusable permission classes and role authority rules."""
from rest_framework.permissions import BasePermission

from apps.core.constants import Roles


def is_platform_admin(user):
    return user.is_authenticated and user.role in Roles.PLATFORM_ROLES


def is_institution_admin(user):
    return user.is_authenticated and user.role in Roles.INSTITUTION_ADMIN_ROLES


def is_content_curator(user):
    return is_platform_admin(user) or (
        user.is_authenticated and user.role == Roles.CONTENT_MANAGER
    )


def can_assign_role(actor, role, institution_id=None):
    """Return True when ``actor`` is allowed to grant ``role``.

    Super admins can grant any role. Platform admins can grant every role
    except SUPER_ADMIN. School and institution admins can only grant roles
    inside their own institution and never a platform role. Ordinary users
    cannot grant roles at all.
    """
    if not actor or not actor.is_authenticated:
        return False
    if actor.role == Roles.SUPER_ADMIN:
        return True
    if actor.role == Roles.PLATFORM_ADMIN:
        return role != Roles.SUPER_ADMIN
    if is_institution_admin(actor):
        if role in Roles.PLATFORM_ROLES:
            return False
        if institution_id is not None and not same_institution(actor, institution_id):
            return False
        return True
    return False


def same_institution(user, institution_id):
    """Platform admins see everything; everyone else is locked to one institution."""
    if is_platform_admin(user):
        return True
    return bool(user.institution_id) and user.institution_id == institution_id


class IsPlatformAdmin(BasePermission):
    message = "Only platform administrators may perform this action."

    def has_permission(self, request, view):
        return is_platform_admin(request.user)


class IsInstitutionAdmin(BasePermission):
    message = "Only institution administrators may perform this action."

    def has_permission(self, request, view):
        return is_platform_admin(request.user) or is_institution_admin(request.user)


class IsContentCurator(BasePermission):
    message = "Only platform administrators and content managers may perform this action."

    def has_permission(self, request, view):
        return is_content_curator(request.user)


class IsStaff(BasePermission):
    message = "Only school staff may perform this action."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role in Roles.STAFF_ROLES)


class IsInstitutionMember(BasePermission):
    """Object-level check using the object's ``institution`` attribute."""

    message = "You cannot access records from another institution."

    def has_object_permission(self, request, view, obj):
        institution = getattr(obj, "institution", None)
        institution_id = getattr(institution, "id", institution)
        return same_institution(request.user, institution_id)


class IsSelfOrInstitutionAdmin(BasePermission):
    """Users may always read their own record; staff may read records in their school."""

    message = "You may only access your own record."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(obj, "id", None) == user.id:
            return True
        return is_institution_admin(user) or is_platform_admin(user)
