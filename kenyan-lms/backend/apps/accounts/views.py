"""Authentication and user management API endpoints."""
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from apps.accounts.models import AdminInvitation, User
from apps.accounts.serializers import (
    AdminInvitationAcceptSerializer, AdminInvitationSerializer, LoginSerializer,
    PasswordChangeSerializer, PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer, PublicRegistrationSerializer,
    UserCreateSerializer, UserSerializer,
)
from apps.core.constants import Roles
from apps.core.permissions import IsInstitutionAdmin, IsPlatformAdmin, is_platform_admin
from apps.core.viewsets import InstitutionScopedQuerysetMixin


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Exchange username/password for an API token."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "user": UserSerializer(user, context={"request": request}).data,
        "must_change_password": user.must_change_password,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
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
    """Delete the current token. The frontend must also discard it."""
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "Logged out."})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """Read or update the logged-in user's own profile."""
    if request.method == "PATCH":
        allowed = ["first_name", "last_name", "email", "phone", "preferred_language"]
        for field in allowed:
            if field in request.data:
                setattr(request.user, field, request.data[field])
        request.user.save()
    return Response(UserSerializer(request.user, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change(request):
    serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password changed."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    # Always the same response: do not reveal which emails exist.
    return Response({"detail": "If the account exists, a reset message has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password reset. You may now log in."})


class UserViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """User management. Only administrators may create or change users."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "set_active"}:
            return [IsAuthenticated(), IsInstitutionAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)
        return queryset.select_related("institution")

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("You cannot delete your own account.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = request.data.get("is_active", not user.is_active)
        user.save(update_fields=["is_active"])
        return Response({"detail": "Account status updated.", "is_active": user.is_active})

    @action(detail=False, methods=["get"])
    def roles(self, request):
        """List available role codes for building role pickers in the UI."""
        return Response([{"value": value, "label": label} for value, label in Roles.CHOICES])


class AdminInvitationViewSet(viewsets.ModelViewSet):
    """Single-use administrator invitations; public redemption is token-gated."""

    serializer_class = AdminInvitationSerializer
    queryset = AdminInvitation.objects.all()

    def get_permissions(self):
        if self.action == "accept":
            return [AllowAny()]
        return [IsAuthenticated(), IsInstitutionAdmin()]

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
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": UserSerializer(user, context={"request": request}).data,
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        invitation = self.get_object()
        invitation.revoked = True
        invitation.save(update_fields=["revoked"])
        return Response(status=status.HTTP_204_NO_CONTENT)
