"""Role- and object-level read scoping for learner-owned records.

The institution-only rule in :class:`apps.core.viewsets.InstitutionScopedQuerysetMixin`
is not enough for family data: every authenticated member of a school would
otherwise read every learner's records. These helpers add the second layer:

* staff and platform users keep their (institution-wide) queryset;
* learners are restricted to the learner record tied to their account;
* guardians are restricted to learners reached through a **verified** link,
  optionally gated on a per-record permission such as ``can_view_fees``;
* everybody else gets an empty set.

They are deliberately defined in the learners app so the fee, attendance and
analytics endpoints can all use exactly the same rules.
"""
from apps.core.constants import Roles
from apps.core.permissions import is_platform_admin, is_staff_user
from apps.learners.models import Learner, LearnerGuardian


def is_wide_reader(user):
    """Staff/platform reads stay institution-wide (see the mixin below)."""
    return bool(
        user and user.is_authenticated
        and (is_platform_admin(user) or is_staff_user(user))
    )


def visible_learner_ids(user, permission=None):
    """Learner ids this user may read, for learner and guardian roles.

    ``permission`` names an optional ``LearnerGuardian`` boolean (for example
    ``can_view_fees``) that a verified link must also grant. An empty queryset
    is returned for unlinked/unverified guardians and for unknown roles, so
    callers fail closed. Staff/platform callers should keep their own
    institution-scoped queryset instead of using these ids (see
    :meth:`FamilyScopedReadMixin.get_queryset`).
    """
    none = Learner.objects.none().values_list("id", flat=True)
    if not user or not user.is_authenticated or is_wide_reader(user):
        return none
    if user.role == Roles.LEARNER:
        return Learner.objects.filter(user=user).values_list("id", flat=True)
    if user.role == Roles.GUARDIAN:
        links = LearnerGuardian.objects.filter(guardian__user=user, is_verified=True)
        if permission:
            links = links.filter(**{permission: True})
        return links.values_list("learner_id", flat=True)
    return none


class FamilyScopedReadMixin:
    """Narrow reads to self/a verified guardian link; staff keep their scope.

    Put this mixin before ``InstitutionScopedQuerysetMixin`` in the ViewSet
    bases. It reuses that mixin's institution filter first, so an id from
    another school is still a 404. ``learner_path`` is the relation from the
    ViewSet's model to Learner (``""`` when the model *is* Learner).
    """

    learner_path = ""
    guardian_permission = None

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if is_wide_reader(user):
            return queryset
        prefix = f"{self.learner_path}__" if self.learner_path else ""
        return queryset.filter(**{
            f"{prefix}id__in": visible_learner_ids(user, self.guardian_permission)
        })
