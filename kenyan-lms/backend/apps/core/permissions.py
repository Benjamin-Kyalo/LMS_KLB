"""Reusable permission classes and role authority rules."""
from rest_framework.permissions import BasePermission

from apps.core.constants import Capabilities, Roles


def custom_capabilities(user):
    """Return the allowlisted capabilities of an active custom-role account."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    if getattr(user, "role", None) != Roles.CUSTOM:
        return set()
    custom_role = getattr(user, "custom_role", None)
    if custom_role is None or not getattr(custom_role, "is_active", False):
        return set()
    values = getattr(custom_role, "permissions", None) or []
    if isinstance(values, dict):
        values = [key for key, enabled in values.items() if enabled]
    return {value for value in values if value in Capabilities.ALL}


def has_capability(user, capability):
    """Super admins and admins hold every capability; custom roles are explicit."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    role = getattr(user, "role", None)
    if role in Roles.ADMIN_ROLES:
        return True
    return capability in custom_capabilities(user)


def is_platform_admin(user):
    """Global authority: the super admin only."""
    return bool(
        user and getattr(user, "is_authenticated", False)
        and getattr(user, "role", None) == Roles.SUPER_ADMIN
    )


def is_institution_admin(user):
    """Unrestricted school authority: super admin or admin."""
    return bool(
        user and getattr(user, "is_authenticated", False)
        and getattr(user, "role", None) in Roles.ADMIN_ROLES
    )


def is_staff_user(user):
    """Accounts that may work with teaching records."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    role = getattr(user, "role", None)
    if role in (Roles.SUPER_ADMIN, Roles.ADMIN, Roles.TEACHER):
        return True
    return bool(custom_capabilities(user) & {
        Capabilities.ADMIN_ACCESS,
        Capabilities.COURSES_MANAGE,
        Capabilities.ASSESSMENTS_MANAGE,
        Capabilities.ATTENDANCE_MANAGE,
        Capabilities.ACADEMICS_MANAGE,
        Capabilities.CONTENT_MANAGE,
        Capabilities.REPORTS_VIEW,
        Capabilities.TUTOR_USE,
    })


def is_content_curator(user):
    return has_capability(user, Capabilities.CONTENT_MANAGE)


def can_assign_role(actor, role, institution_id=None, custom_role=None):
    """Return True when ``actor`` is allowed to grant ``role``.

    A super admin may grant anything. An admin may grant every role except
    SUPER_ADMIN inside their own institution. A custom role needs
    ``users.manage``; it can grant ordinary roles and custom roles it is
    allowed to manage, never an admin role.
    """
    if not actor or not getattr(actor, "is_authenticated", False):
        return False
    actor_role = getattr(actor, "role", None)
    if actor_role == Roles.SUPER_ADMIN:
        return role != Roles.CUSTOM or custom_role is not None
    if role == Roles.SUPER_ADMIN:
        return False

    if actor_role == Roles.ADMIN:
        if institution_id is not None and not same_institution(actor, institution_id):
            return False
        if role == Roles.CUSTOM:
            return bool(
                custom_role
                and getattr(custom_role, "is_active", False)
                and same_institution(actor, getattr(custom_role, "institution_id", None))
            )
        return role in Roles.ASSIGNABLE_BUILTINS

    capabilities = custom_capabilities(actor)
    if Capabilities.USERS_MANAGE not in capabilities:
        return False
    if institution_id is not None and not same_institution(actor, institution_id):
        return False
    if role == Roles.CUSTOM:
        return (
            Capabilities.ROLES_MANAGE in capabilities
            and custom_role is not None
            and getattr(custom_role, "is_active", False)
            and same_institution(actor, getattr(custom_role, "institution_id", None))
        )
    return role in {Roles.TEACHER, Roles.LEARNER, Roles.GUARDIAN}


def same_institution(user, institution_id):
    """Super admins see everything; everyone else is locked to one institution."""
    if is_platform_admin(user):
        return True
    return bool(getattr(user, "institution_id", None)) and user.institution_id == institution_id


class IsSuperAdmin(BasePermission):
    message = "Only the super administrator may perform this action."

    def has_permission(self, request, view):
        return is_platform_admin(request.user)


# Legacy name retained for the small number of call sites where the message is
# user-facing; the rule is now super-admin only.
IsPlatformAdmin = IsSuperAdmin


class IsInstitutionAdmin(BasePermission):
    message = "Only an administrator may perform this action."

    def has_permission(self, request, view):
        return is_institution_admin(request.user)


class HasCapability(BasePermission):
    """Allow full admins and custom roles with the named capability."""

    capability = None
    message = "Your role does not have permission for this action."

    def has_permission(self, request, view):
        return bool(self.capability and has_capability(request.user, self.capability))


_CAPABILITY_PERMISSIONS = {}


def capability_permission(capability):
    """Return a no-argument DRF permission class for ``capability``."""
    if capability not in Capabilities.ALL:
        raise ValueError(f"Unknown capability: {capability}")
    if capability not in _CAPABILITY_PERMISSIONS:
        name = "Can" + "".join(part.title() for part in capability.replace(".", "_").split("_"))
        _CAPABILITY_PERMISSIONS[capability] = type(
            name, (HasCapability,), {
                "capability": capability,
                "__module__": __name__,
            }
        )
    return _CAPABILITY_PERMISSIONS[capability]


class IsStaff(BasePermission):
    message = "Only school staff may perform this action."

    def has_permission(self, request, view):
        return is_staff_user(request.user)


class IsStaffOrCapability(BasePermission):
    """Teaching staff or a custom role with a specific capability."""

    capability = None
    message = "Your role does not have permission for this action."

    def has_permission(self, request, view):
        return bool(
            is_staff_user(request.user)
            or (self.capability and has_capability(request.user, self.capability))
        )


_STAFF_CAPABILITY_PERMISSIONS = {}


def staff_or_capability_permission(capability):
    if capability not in Capabilities.ALL:
        raise ValueError(f"Unknown capability: {capability}")
    if capability not in _STAFF_CAPABILITY_PERMISSIONS:
        name = "StaffOr" + "".join(
            part.title() for part in capability.replace(".", "_").split("_")
        )
        _STAFF_CAPABILITY_PERMISSIONS[capability] = type(
            name, (IsStaffOrCapability,), {
                "capability": capability,
                "__module__": __name__,
            }
        )
    return _STAFF_CAPABILITY_PERMISSIONS[capability]


class IsContentCurator(BasePermission):
    message = "Only users who can manage content may perform this action."

    def has_permission(self, request, view):
        return is_content_curator(request.user)


class IsInstitutionMember(BasePermission):
    """Object-level check using the object's ``institution`` attribute."""

    message = "You cannot access records from another institution."

    def has_object_permission(self, request, view, obj):
        institution = getattr(obj, "institution", None)
        institution_id = getattr(institution, "id", institution)
        return same_institution(request.user, institution_id)


class IsSelfOrInstitutionAdmin(BasePermission):
    """Users may always read their own record; admins may read their school."""

    message = "You may only access your own record."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(obj, "id", None) == user.id:
            return True
        return is_institution_admin(user)
