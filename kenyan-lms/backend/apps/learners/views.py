"""Learner API endpoints, including safe CSV import."""
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import OnboardingProfile
from apps.core.audit import log_audit
from apps.core.constants import Capabilities, Roles
from apps.core.permissions import capability_permission, is_institution_admin, is_platform_admin
from apps.core.viewsets import AdminWriteMixin, InstitutionScopedQuerysetMixin
from apps.learners.models import GuardianLinkRequest, Learner, LearnerGuardian, TransferRecord
from apps.learners.serializers import (
    BulkImportSerializer, GuardianLinkDecisionSerializer,
    GuardianLinkRequestCreateSerializer, GuardianLinkRequestSerializer,
    LearnerCreateSerializer, LearnerGuardianSerializer, LearnerSerializer,
    TransferRecordSerializer,
)
from apps.learners.scoping import FamilyScopedReadMixin


class LearnerViewSet(
    FamilyScopedReadMixin, AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet
):
    capability = Capabilities.LEARNERS_MANAGE
    queryset = Learner.objects.select_related("user", "institution", "class_room")
    serializer_class = LearnerSerializer
    filterset_fields = ["institution", "class_room", "status", "gender"]
    search_fields = ["user__first_name", "user__last_name", "admission_number", "assessment_number"]
    # The read serializer contains PII; a guardian only gets it for a child
    # linked by a verified record that allows academic/profile access.
    guardian_permission = "can_view_academics"

    def get_queryset(self):
        return super().get_queryset().select_related("user", "class_room", "institution")

    def get_serializer_class(self):
        if self.action == "create":
            return LearnerCreateSerializer
        return LearnerSerializer

    def create(self, request, *args, **kwargs):
        """Return the created learner using the read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        learner = serializer.save()
        output = LearnerSerializer(learner, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        serializer = BulkImportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        learners = serializer.save()
        return Response({"imported": len(learners)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def guardians(self, request, pk=None):
        learner = self.get_object()
        links = LearnerGuardian.objects.filter(learner=learner).select_related("guardian__user")
        return Response(LearnerGuardianSerializer(links, many=True).data)


class LearnerGuardianViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """
    LearnerGuardian has no institution field, so the mixin cannot filter it.
    We override get_queryset to scope through the learner instead.
    """

    capability = Capabilities.LEARNERS_MANAGE
    serializer_class = LearnerGuardianSerializer

    def get_queryset(self):
        from apps.core.permissions import is_platform_admin
        qs = LearnerGuardian.objects.select_related("learner", "guardian__user")
        if is_platform_admin(self.request.user):
            return qs
        if self.request.user.institution_id:
            return qs.filter(learner__institution_id=self.request.user.institution_id)
        return qs.none()


class GuardianLinkRequestViewSet(viewsets.ModelViewSet):
    """Guardian-submitted links; only verified links grant report access."""

    serializer_class = GuardianLinkRequestSerializer
    # Requests move through create/verify/reject only. Generic PATCH/DELETE
    # would let a caller flip status without creating the verified grant.
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in {"verify", "reject"}:
            return [
                IsAuthenticated(),
                capability_permission(Capabilities.GUARDIANS_MANAGE)(),
            ]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return GuardianLinkRequest.objects.none()
        qs = GuardianLinkRequest.objects.select_related(
            "guardian__user", "learner__user", "decided_by", "institution"
        )
        if is_platform_admin(user):
            return qs
        if is_institution_admin(user) and user.institution_id:
            return qs.filter(institution_id=user.institution_id)
        if user.role == Roles.GUARDIAN:
            return qs.filter(guardian__user=user)
        return qs.none()

    def get_serializer_class(self):
        if self.action == "create":
            return GuardianLinkRequestCreateSerializer
        return GuardianLinkRequestSerializer

    @staticmethod
    def _find_learner(identifier, institution_id):
        identifier = (identifier or "").strip()
        if not identifier:
            return None
        return (
            Learner.objects.filter(
                institution_id=institution_id, admission_number__iexact=identifier
            ).first()
            or Learner.objects.filter(
                institution_id=institution_id, assessment_number__iexact=identifier
            ).first()
        )

    def create(self, request, *args, **kwargs):
        if request.user.role != Roles.GUARDIAN:
            raise PermissionDenied("Only guardians can submit learner link requests.")
        guardian = getattr(request.user, "guardian_profile", None)
        if guardian is None:
            raise ValidationError("Your guardian profile is missing. Contact your school.")

        payload = GuardianLinkRequestCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        identifier = payload.validated_data["learner_identifier"]
        learner = self._find_learner(identifier, request.user.institution_id)
        if learner is None:
            # Do not confirm whether an identifier exists anywhere: the same
            # response covers unknown numbers and learners at other schools.
            raise ValidationError({
                "learner_identifier": (
                    "The learner details could not be linked. Check the school and "
                    "learner number or contact the office."
                )
            })
        if LearnerGuardian.objects.filter(learner=learner, guardian=guardian).exists():
            raise ValidationError("This learner is already linked to your account.")
        if GuardianLinkRequest.objects.filter(
            learner=learner, guardian=guardian, status="PENDING"
        ).exists():
            raise ValidationError("A link request for this learner is already pending.")

        link_request = GuardianLinkRequest.objects.create(
            institution=request.user.institution,
            guardian=guardian,
            learner=learner,
            learner_identifier=identifier.strip(),
            relationship=payload.validated_data.get("relationship", ""),
            status="PENDING",
        )
        return Response(
            GuardianLinkRequestSerializer(link_request).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def verify(self, request, pk=None):
        link_request = self.get_object()
        if link_request.status != "PENDING":
            raise ValidationError("Only pending guardian links can be verified.")

        payload = GuardianLinkDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        link, _ = LearnerGuardian.objects.get_or_create(
            learner=link_request.learner,
            guardian=link_request.guardian,
            defaults={
                "relationship": data.get("relationship") or link_request.relationship,
                "is_verified": True,
                "is_primary": data.get("is_primary", False),
            },
        )
        if not link.is_verified:
            # An older or manually stubbed link must not stay invisible to the
            # report scoping queries after this explicit verification.
            link.is_verified = True
            link.save(update_fields=["is_verified"])
        link_request.status = "VERIFIED"
        link_request.verified_link = link
        link_request.notes = data.get("notes", "")
        link_request.decided_by = request.user
        link_request.decided_at = timezone.now()
        link_request.save(update_fields=[
            "status", "verified_link", "notes", "decided_by", "decided_at", "updated_at"
        ])

        profile, _ = OnboardingProfile.objects.get_or_create(user=link_request.guardian.user)
        profile.guardian_link_verified = True
        profile.mark_complete_if_ready()
        profile.save(update_fields=["guardian_link_verified", "completed_at", "updated_at"])

        log_audit(
            request.user, "verify", "GuardianLinkRequest", link_request.pk,
            {"guardian": link_request.guardian_id, "learner": link_request.learner_id},
            institution=link_request.institution, request=request,
        )
        return Response(GuardianLinkRequestSerializer(link_request).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        link_request = self.get_object()
        if link_request.status != "PENDING":
            raise ValidationError("Only pending guardian links can be rejected.")
        notes = (request.data.get("notes") or "").strip()
        if not notes:
            raise ValidationError({"notes": "Give a short reason for rejecting this link."})

        link_request.status = "REJECTED"
        link_request.notes = notes
        link_request.decided_by = request.user
        link_request.decided_at = timezone.now()
        link_request.save(update_fields=["status", "notes", "decided_by", "decided_at", "updated_at"])

        log_audit(
            request.user, "reject", "GuardianLinkRequest", link_request.pk,
            {"guardian": link_request.guardian_id, "learner": link_request.learner_id},
            institution=link_request.institution, request=request,
        )
        return Response(GuardianLinkRequestSerializer(link_request).data)


class TransferRecordViewSet(AdminWriteMixin, viewsets.ModelViewSet):
    capability = Capabilities.LEARNERS_MANAGE
    serializer_class = TransferRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TransferRecord.objects.select_related("learner__user")
        if self.request.user.is_platform_user:
            return qs
        if self.request.user.institution_id:
            return qs.filter(learner__institution_id=self.request.user.institution_id)
        return qs.none()
