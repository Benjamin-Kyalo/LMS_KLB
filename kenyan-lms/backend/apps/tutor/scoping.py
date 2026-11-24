"""Shared access rules for tutor conversations and their message history.

Staff see every conversation in their institution. Learners see conversations
they started or that are attached to their own learner record. Guardians see
conversations they started or that are attached to a learner they are linked
to. These helpers are used by both querysets and object-level permissions so
the two cannot disagree.
"""
from django.db.models import Q

from apps.core.constants import Roles
from apps.guardians.models import Guardian
from apps.learners.models import Learner, LearnerGuardian
from apps.tutor.models import TutorConversation


def is_tutor_staff(user):
    return bool(
        user.is_authenticated
        and user.role in Roles.STAFF_ROLES
    )


def linked_learner_ids(user):
    """Learner ids the user may reasonably work with, or None for staff."""
    if not user.is_authenticated or not user.institution_id:
        return []
    if is_tutor_staff(user):
        return None  # no extra restriction beyond institution scoping
    if user.role == Roles.LEARNER:
        learner = Learner.objects.filter(
            user=user, institution_id=user.institution_id
        ).first()
        return [learner.pk] if learner else []
    if user.role == Roles.GUARDIAN:
        guardian = Guardian.objects.filter(user=user).first()
        if guardian is None:
            return []
        return list(
            LearnerGuardian.objects.filter(
                guardian=guardian, learner__institution_id=user.institution_id
            ).values_list("learner_id", flat=True)
        )
    return []


def can_use_tutor(user):
    return bool(
        user.is_authenticated
        and user.institution_id
        and (is_tutor_staff(user) or user.role in (Roles.LEARNER, Roles.GUARDIAN))
    )


def scoped_conversations(user, queryset=None):
    """Filter a TutorConversation queryset to what ``user`` may see."""
    queryset = queryset if queryset is not None else TutorConversation.objects.all()
    if not user.is_authenticated or not user.institution_id:
        return queryset.none()
    queryset = queryset.filter(institution_id=user.institution_id)
    if is_tutor_staff(user):
        return queryset
    learner_ids = linked_learner_ids(user) or []
    own = Q(started_by=user)
    if learner_ids:
        return queryset.filter(own | Q(learner_id__in=learner_ids))
    return queryset.filter(own)


def may_manage_conversation(user, conversation):
    if conversation is None or not user.is_authenticated:
        return False
    if not user.institution_id or conversation.institution_id != user.institution_id:
        return False
    if is_tutor_staff(user):
        return True
    learner_ids = linked_learner_ids(user) or []
    return (
        conversation.started_by_id == user.pk
        or (bool(learner_ids) and conversation.learner_id in learner_ids)
    )


def validate_learner_choice(user, learner):
    """Return an allowed learner for non-staff writes, or raise a clear error."""
    from rest_framework.exceptions import ValidationError

    if is_tutor_staff(user):
        return learner
    learner_ids = linked_learner_ids(user) or []
    if learner is None:
        if len(learner_ids) == 1:
            return Learner.objects.get(pk=learner_ids[0])
        raise ValidationError(
            {"learner": "Choose one of your own learner records."}
        )
    if learner.pk not in learner_ids:
        raise ValidationError({"learner": "You cannot use another learner's record."})
    return learner
