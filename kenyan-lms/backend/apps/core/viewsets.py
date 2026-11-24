"""ViewSet mixins that enforce institution isolation and write authority."""
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import (
    IsContentCurator, IsInstitutionAdmin, IsPlatformAdmin, IsStaff, is_platform_admin,
)
from apps.institutions.models import Institution

READ_ACTIONS = {"list", "retrieve"}


class InstitutionScopedQuerysetMixin:
    """
    Add this mixin to a ViewSet whose model has an ``institution`` field.

    Platform admins receive all rows. Every other user receives only rows
    from their own institution. If a user has no institution, they get
    nothing - fail closed, never open.

    The mixin also:
    - supplies a default queryset when a ViewSet has not set one explicitly,
      by reading the serializer's Meta.model;
    - forces ``institution`` to the current user's institution on create and
      update, so a client cannot smuggle another school's ID in the payload.
      Models without an institution field (e.g. LearnerGuardian, Rubric) are
      left alone; their ViewSets scope through a related object where needed.

    Keeping all of this here means one rule protects every app.
    """

    # Deterministic pagination: without a default ordering Django warns and
    # page boundaries can shift between requests.
    ordering = ["id"]

    def _model(self):
        serializer_class = getattr(self, "serializer_class", None)
        if serializer_class is None:
            serializer_class = self.get_serializer_class()
        return getattr(getattr(serializer_class, "Meta", None), "model", None)

    def _has_institution_field(self):
        model = self._model()
        if model is None:
            return False
        return any(field.name == "institution" for field in model._meta.get_fields())

    def _base_queryset(self):
        """Build the unfiltered queryset without recursing into this mixin."""
        queryset = getattr(self, "queryset", None)
        if queryset is not None:
            return queryset.all()
        model = self._model()
        if model is not None:
            return model.objects.all()
        # No model can be derived: let DRF raise its normal helpful assertion.
        return super().get_queryset()

    def get_queryset(self):
        queryset = self._base_queryset()

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if is_platform_admin(user):
            return queryset
        if user.institution_id:
            return queryset.filter(institution_id=user.institution_id)
        return queryset.none()

    def _scoped_save(self, serializer, **kwargs):
        user = self.request.user
        if self._has_institution_field() and "institution" not in kwargs:
            if not is_platform_admin(user):
                # save(**kwargs) overrides anything the client supplied in
                # validated_data, so the payload cannot choose an institution.
                kwargs["institution"] = user.institution
            elif "institution" in self.request.data and self.request.data["institution"]:
                # Platform admins may work across schools. Some serializers
                # mark institution read-only, so accept the explicit choice
                # here after checking that the school really exists.
                try:
                    kwargs["institution"] = Institution.objects.get(
                        pk=self.request.data["institution"]
                    )
                except (Institution.DoesNotExist, ValueError, TypeError) as exc:
                    raise ValidationError({"institution": "Choose a valid institution."}) from exc
            elif user.institution_id:
                kwargs["institution"] = user.institution
        serializer.save(**kwargs)

    def perform_create(self, serializer):
        self._scoped_save(serializer)

    def perform_update(self, serializer):
        self._scoped_save(serializer)


class AdminWriteMixin:
    """Read for authenticated users, write for administrators.

    This closes the common gap where a ViewSet relied only on DRF's global
    ``IsAuthenticated`` setting and therefore let any learner mutate school
    records. Custom actions that change state are writes too.
    """

    write_permission_classes = (IsInstitutionAdmin,)

    def get_permissions(self):
        if self.action in READ_ACTIONS:
            return [IsAuthenticated()]
        return [IsAuthenticated()] + [cls() for cls in self.write_permission_classes]


class StaffWriteMixin(AdminWriteMixin):
    """Teaching records may be changed by teachers and administrators."""

    write_permission_classes = (IsStaff,)


class PlatformWriteMixin(AdminWriteMixin):
    """Global reference data may only be changed by platform administrators."""

    write_permission_classes = (IsPlatformAdmin,)


class ContentWriteMixin(AdminWriteMixin):
    """Publishing data may be changed by platform admins or content managers."""

    write_permission_classes = (IsContentCurator,)
