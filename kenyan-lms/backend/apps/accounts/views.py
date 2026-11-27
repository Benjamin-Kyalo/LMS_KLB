"""Authentication and user management API endpoints."""
import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password as validate_password_value
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db import transaction
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from apps.accounts.models import AdminInvitation, CustomRole, OnboardingProfile, User
from apps.accounts.security import (
    assert_login_allowed, invalidate_user_sessions, record_failed_login,
    record_reset_request, record_successful_login, reset_request_count,
)
from apps.core.audit import log_audit
from apps.core.throttling import (
    LoginThrottle, PasswordResetThrottle, RegistrationThrottle,
)
from apps.accounts.serializers import (
    AdminInvitationAcceptSerializer, AdminInvitationSerializer, CustomRoleSerializer,
    LoginSerializer, OnboardingProfileSerializer, PasswordChangeSerializer,
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
    PublicRegistrationSerializer, UserCreateSerializer, UserProfileUpdateSerializer,
    UserSerializer,
)
from apps.core.constants import Capabilities, Roles
from apps.core.permissions import (
    capability_permission, has_capability, is_institution_admin, is_platform_admin,
    is_staff_user,
)
from apps.core.viewsets import InstitutionScopedQuerysetMixin
from apps.institutions.models import Institution
from apps.learners.models import Learner
from apps.teachers.models import TeacherApproval


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_token(request):
    """Issue the CSRF cookie used by the session-authenticated SPA."""
    return Response({"detail": "CSRF cookie set."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    """Create a Django session after checking credentials and throttling."""
    username = request.data.get("username", "")
    assert_login_allowed(request, username)
    serializer = LoginSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
    except Exception:
        record_failed_login(request, username)
        raise
    user = serializer.validated_data["user"]
    auth_login(request, user)
    record_successful_login(request, username)
    return Response({
        "user": UserSerializer(user, context={"request": request}).data,
        "must_change_password": user.must_change_password,
        "csrfToken": get_token(request),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register(request):
    """Role-based public signup. Admin roles cannot be requested here."""
    serializer = PublicRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({
        "detail": (
            "Account created. A school administrator must approve teacher accounts "
            "before they can sign in."
            if user.role == Roles.TEACHER else "Account created. You may now sign in."
        ),
        "user": UserSerializer(user, context={"request": request}).data,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """End the browser session and revoke any legacy API token."""
    user = request.user
    Token.objects.filter(user=user).delete()
    auth_logout(request)
    return Response({"detail": "Logged out."})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """Read or update the logged-in user's own profile."""
    if request.method == "PATCH":
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(UserSerializer(request.user, context={"request": request}).data)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def onboarding_me(request):
    """Read or confirm the caller's own first-run checklist."""
    profile, _ = OnboardingProfile.objects.get_or_create(user=request.user)
    if request.method == "PATCH":
        serializer = OnboardingProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile = serializer.instance
    return Response(OnboardingProfileSerializer(profile).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change(request):
    serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password changed."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    if reset_request_count(request, email) < settings.RESET_REQUEST_MAX:
        serializer.save()
        record_reset_request(request, email)
    # Always the same response: do not reveal which emails exist or whether a
    # request was suppressed by the abuse window.
    return Response({
        "detail": (
            "Password reset instructions have been sent to the registered email "
            "address, if an account matches the details provided."
        )
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password reset. You may now log in."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def learner_lookup(request):
    """Return limited learner details for guardian registration confirmation."""
    institution_id = request.data.get("institution")
    identifier = str(request.data.get("learner_identifier", "") or "").strip()
    if not institution_id or not identifier:
        raise ValidationError({"detail": "School and learner number are required."})
    try:
        institution = Institution.objects.get(pk=institution_id, is_active=True)
    except (Institution.DoesNotExist, ValueError, TypeError):
        raise ValidationError({"institution": "Choose a valid school."})
    learner = (
        Learner.objects.filter(institution=institution, admission_number__iexact=identifier).first()
        or Learner.objects.filter(institution=institution, assessment_number__iexact=identifier).first()
    )
    if learner is None:
        return Response(
            {"detail": "No learner was found with that admission or assessment number in the selected school. Check the number and school, then try again."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({
        "found": True,
        "learner": {
            "full_name": learner.user.full_name,
            "admission_number": learner.admission_number,
            "assessment_number": learner.assessment_number,
            "class_name": getattr(learner.class_room, "display_name", ""),
        },
    })


class UserViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """User management. Only administrators may create or change users."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "set_active", "reset_password"}:
            return [IsAuthenticated(), capability_permission(Capabilities.USERS_MANAGE)()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)
        user = self.request.user
        if user.is_authenticated and not is_staff_user(user):
            # Learners and guardians have no reason to enumerate accounts.
            queryset = queryset.filter(pk=user.pk)
        return queryset.select_related("institution")

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reset_password(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError("Use the password change form for your own account.")
        alphabet = string.ascii_letters + string.digits
        temporary_password = None
        for _ in range(20):
            candidate = "".join(secrets.choice(alphabet) for _ in range(12))
            try:
                validate_password_value(candidate, user)
                temporary_password = candidate
                break
            except DjangoValidationError:
                continue
        if temporary_password is None:
            raise ValidationError("Could not generate a valid temporary password.")
        user.set_password(temporary_password)
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])
        # Keep the administrator's own session alive while ending every session
        # that belongs to the account being reset.
        invalidate_user_sessions(user, keep_session_key=request.session.session_key)
        log_audit(
            request.user, "password_reset", "User", user.pk,
            {"username": user.username}, institution=user.institution, request=request,
        )
        return Response({
            "detail": "Temporary password generated. The user must change it on next sign-in.",
            "temporary_password": temporary_password,
        })

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("You cannot delete your own account.")
        instance.delete()

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def set_active(self, request, pk=None):
        user = self.get_object()
        desired = request.data.get("is_active", not user.is_active)
        if user.role == Roles.TEACHER and desired:
            approved = TeacherApproval.objects.filter(
                teacher=user.teacher_profile, status="APPROVED"
            ).exists()
            if not approved:
                raise ValidationError(
                    "Approve this teacher in the approval queue before activating the account."
                )
        user.is_active = desired
        user.save(update_fields=["is_active"])
        teacher_profile = getattr(user, "teacher_profile", None)
        if teacher_profile is not None:
            teacher_profile.is_active = desired
            teacher_profile.save(update_fields=["is_active"])
            if desired:
                profile, _ = OnboardingProfile.objects.get_or_create(user=user)
                profile.teacher_approved = True
                if teacher_profile.assignments.exists():
                    profile.classes_assigned = True
                profile.mark_complete_if_ready()
                profile.save(update_fields=[
                    "teacher_approved", "classes_assigned", "completed_at", "updated_at"
                ])
        log_audit(
            request.user, "set_active", "User", user.pk,
            {"is_active": desired, "role": user.role},
            institution=user.institution, request=request,
        )
        return Response({"detail": "Account status updated.", "is_active": user.is_active})

    @action(detail=False, methods=["get"])
    def roles(self, request):
        """Role options the caller may assign, including custom roles."""
        user = request.user
        labels = dict(Roles.CHOICES)
        options = []

        def builtin(value):
            return {
                "value": value,
                "label": labels[value],
                "kind": "builtin",
                "capabilities": [],
            }

        if is_platform_admin(user):
            options.extend(builtin(value) for value in [
                Roles.SUPER_ADMIN, Roles.ADMIN, Roles.TEACHER,
                Roles.LEARNER, Roles.GUARDIAN,
            ])
        elif is_institution_admin(user):
            options.extend(builtin(value) for value in [
                Roles.ADMIN, Roles.TEACHER, Roles.LEARNER, Roles.GUARDIAN,
            ])
        elif has_capability(user, Capabilities.USERS_MANAGE):
            options.extend(builtin(value) for value in [
                Roles.TEACHER, Roles.LEARNER, Roles.GUARDIAN,
            ])

        if options:
            custom_roles = CustomRole.objects.filter(is_active=True)
            if not is_platform_admin(user) and user.institution_id:
                custom_roles = custom_roles.filter(institution_id=user.institution_id)
            else:
                custom_roles = custom_roles.none() if not is_platform_admin(user) else custom_roles
            options.extend({
                "value": Roles.CUSTOM,
                "label": role.name,
                "kind": "custom",
                "custom_role": role.pk,
                "capabilities": role.capabilities,
            } for role in custom_roles)
        return Response(options)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def capabilities(request):
    """Permission catalogue for the custom-role picker."""
    return Response([{
        "group": group,
        "items": [{
            "value": value,
            "label": Capabilities.LABELS[value],
        } for value in values],
    } for group, values in Capabilities.GROUPS])


class CustomRoleViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Administrator-managed custom roles with explicit capabilities."""

    serializer_class = CustomRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated(), capability_permission(Capabilities.ROLES_MANAGE)()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        with transaction.atomic():
            super().perform_create(serializer)
            log_audit(
                self.request.user, "custom_role.created", "CustomRole", serializer.instance.pk,
                {"name": serializer.instance.name, "permissions": serializer.instance.permissions},
                institution=serializer.instance.institution, request=self.request,
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            super().perform_update(serializer)
            log_audit(
                self.request.user, "custom_role.updated", "CustomRole", serializer.instance.pk,
                {"name": serializer.instance.name, "permissions": serializer.instance.permissions},
                institution=serializer.instance.institution, request=self.request,
            )

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            role = self.get_object()
            if role.users.exists() or role.invitations.exists():
                role.is_active = False
                role.save(update_fields=["is_active", "updated_at"])
                log_audit(
                    request.user, "custom_role.deactivated", "CustomRole", role.pk,
                    {"name": role.name}, institution=role.institution, request=request,
                )
            else:
                role_pk, institution = role.pk, role.institution
                role.delete()
                log_audit(
                    request.user, "custom_role.deleted", "CustomRole", role_pk,
                    {}, institution=institution, request=request,
                )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminInvitationViewSet(viewsets.ModelViewSet):
    """Single-use administrator invitations; public redemption is token-gated."""

    serializer_class = AdminInvitationSerializer
    queryset = AdminInvitation.objects.all()

    def get_permissions(self):
        if self.action == "accept":
            return [AllowAny()]
        return [IsAuthenticated(), capability_permission(Capabilities.USERS_MANAGE)()]

    def get_serializer_class(self):
        if self.action == "accept":
            return AdminInvitationAcceptSerializer
        return AdminInvitationSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return AdminInvitation.objects.none()
        if is_platform_admin(user):
            return AdminInvitation.objects.select_related("institution", "invited_by")
        if user.institution_id:
            return AdminInvitation.objects.filter(institution_id=user.institution_id)
        return AdminInvitation.objects.none()

    @action(detail=False, methods=["post"])
    def accept(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        auth_login(request, user)
        return Response({
            "user": UserSerializer(user, context={"request": request}).data,
            "csrfToken": get_token(request),
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        invitation = self.get_object()
        invitation.revoked = True
        invitation.save(update_fields=["revoked"])
        return Response(status=status.HTTP_204_NO_CONTENT)
