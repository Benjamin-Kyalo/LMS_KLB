"""Shared access rules for reports and analytics.

Keeping these rules in one module prevents the dashboard and the chart data
endpoint from disagreeing about what a user may see.
"""
from apps.core.constants import Roles
from apps.core.permissions import is_platform_admin, is_staff_user
from apps.learners.models import LearnerGuardian


def scoped_institution_id(user):
    """Return the institution to report on.

    ``None`` means a genuine platform-wide view. A non-platform user without an
    institution gets ``0`` so every filter returns an empty set instead of
    accidentally exposing all schools.
    """
    if is_platform_admin(user):
        return None
    return user.institution_id or 0


def dashboard_viewer(user):
    """Only staff and platform administrators see school-wide dashboards."""
    return bool(user.is_authenticated) and (is_staff_user(user) or is_platform_admin(user))


def guardian_link(user, learner):
    if user.role != Roles.GUARDIAN:
        return None
    return (
        LearnerGuardian.objects.filter(
            learner=learner, guardian__user=user, is_verified=True
        )
        .select_related("guardian")
        .first()
    )


def can_view_learner(user, learner):
    """Check whether this user may open an individual learner report."""
    if is_platform_admin(user) or is_staff_user(user):
        return scoped_institution_id(user) in (None, learner.institution_id)
    if user.role == Roles.LEARNER:
        return learner.user_id == user.id
    if user.role == Roles.GUARDIAN:
        return guardian_link(user, learner) is not None
    return False
