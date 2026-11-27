"""Serializers for authentication and user management."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.db import IntegrityError, transaction
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

import re

from apps.accounts.models import (
    AdminInvitation, CustomRole, OnboardingProfile, PasswordResetUse, User,
)


def _generate_username(first_name, last_name):
    base = f"{first_name}_{last_name}".strip("_").lower().replace(" ", "_")
    base = re.sub(r"[^a-z0-9_.-]", "", base)
    base = re.sub(r"_+", "_", base).strip("_.-")
    if not base:
        base = "user"
    candidate = base
    counter = 2
    while User.objects.filter(username__iexact=candidate).exists():
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate
from apps.accounts.security import hash_reset_token, invalidate_user_sessions
from apps.core.constants import Capabilities, Roles
from apps.core.permissions import (
    can_assign_role, has_capability, is_institution_admin, is_platform_admin,
    same_institution,
)
from apps.guardians.models import Guardian
from apps.institutions.models import Institution
from apps.learners.models import GuardianLinkRequest, Learner
from apps.teachers.models import Teacher, TeacherApproval


def _actor_institution(actor, raw_value=None):
    """Admins are pinned to their school; only the super admin chooses one."""
    if is_institution_admin(actor) and not is_platform_admin(actor):
        return actor.institution_id
    try:
        return int(raw_value) if raw_value not in (None, "") else None
    except (TypeError, ValueError):
        return raw_value


def _resolve_custom_role(actor, value):
    if value in (None, ""):
        return None
    if isinstance(value, CustomRole):
        return value
    try:
        return CustomRole.objects.get(pk=int(value))
    except (TypeError, ValueError, CustomRole.DoesNotExist):
        raise serializers.ValidationError({"custom_role": "Choose a valid custom role."})


def _validate_role_assignment(actor, role, institution_id, custom_role):
    if not can_assign_role(actor, role, institution_id, custom_role):
        raise serializers.ValidationError({"role": "You are not allowed to assign this role."})


class OnboardingProfileSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    role = serializers.CharField(source="user.role", read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    steps = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingProfile
        fields = [
            "role", "profile_complete", "teacher_approved", "classes_assigned",
            "guardian_link_verified", "is_complete", "steps", "completed_at",
        ]
        read_only_fields = [
            "role", "teacher_approved", "classes_assigned", "guardian_link_verified",
            "is_complete", "steps", "completed_at",
        ]

    def get_steps(self, obj):
        return obj.steps()

    @transaction.atomic
    def update(self, instance, validated_data):
        # The owner may only confirm their own details; workflow flags remain
        # server-controlled.
        allowed = {"profile_complete"}
        for field in list(validated_data):
            if field not in allowed:
                validated_data.pop(field)
        instance = super().update(instance, validated_data)
        instance.mark_complete_if_ready()
        return instance


class UserSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_code = serializers.CharField(source="institution.code", read_only=True)
    institution_logo = serializers.SerializerMethodField()
    onboarding = serializers.SerializerMethodField()
    relationship_to_learner = serializers.SerializerMethodField()
    custom_role_name = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()
    admission_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name",
            "role", "custom_role", "custom_role_name", "capabilities",
            "admission_number",
            "institution", "institution_name", "institution_code",
            "institution_logo", "phone", "preferred_language", "is_active",
            "must_change_password", "onboarding", "relationship_to_learner",
            "date_joined", "last_login",
        ]
        read_only_fields = [
            "id", "date_joined", "last_login", "full_name", "custom_role_name",
            "capabilities", "institution_name", "institution_code",
            "institution_logo", "onboarding", "relationship_to_learner",
        ]

    def get_institution_logo(self, obj):
        if not obj.institution_id or not obj.institution.logo:
            return None
        request = self.context.get("request")
        url = obj.institution.logo.url
        return request.build_absolute_uri(url) if request else url

    def get_onboarding(self, obj):
        profile, _ = OnboardingProfile.objects.get_or_create(user=obj)
        return OnboardingProfileSerializer(profile).data

    def get_relationship_to_learner(self, obj):
        guardian = getattr(obj, "guardian_profile", None)
        return guardian.relationship_to_learner if guardian else ""

    def get_custom_role_name(self, obj):
        if obj.role == Roles.CUSTOM and obj.custom_role_id:
            return obj.custom_role.name
        return ""

    def get_capabilities(self, obj):
        return obj.capabilities

    def get_admission_number(self, obj):
        learner = getattr(obj, "learner_profile", None)
        return getattr(learner, "admission_number", "") or ""

    def validate(self, attrs):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if not actor or not actor.is_authenticated:
            return attrs

        role = attrs.get("role", getattr(self.instance, "role", None))
        institution = attrs.get("institution", getattr(self.instance, "institution", None))
        institution_id = _actor_institution(actor, getattr(institution, "id", institution))
        custom_role_raw = attrs.get(
            "custom_role", getattr(self.instance, "custom_role", None)
        )
        custom_role = _resolve_custom_role(actor, custom_role_raw)

        if role == Roles.CUSTOM:
            if custom_role is None:
                raise serializers.ValidationError({
                    "custom_role": "Choose a custom role for this account."
                })
            if not is_platform_admin(actor):
                custom_institution = getattr(custom_role, "institution_id", None)
                if custom_institution is not None and custom_institution != institution_id:
                    raise serializers.ValidationError({
                        "custom_role": "Choose a custom role from this institution."
                    })
            attrs["custom_role"] = custom_role
        else:
            attrs.pop("custom_role", None)
            custom_role = None

        if self.instance and self.instance.pk == actor.pk:
            changing_role = (
                "role" in attrs and role != actor.role
            ) or (
                "custom_role" in attrs and self.instance.custom_role != custom_role
            )
            if changing_role:
                raise serializers.ValidationError({"role": "You cannot change your own role."})
            if "is_active" in attrs and not attrs["is_active"]:
                raise serializers.ValidationError({"is_active": "You cannot deactivate your own account."})
            if "institution" in attrs and not is_platform_admin(actor):
                raise serializers.ValidationError({"institution": "You cannot move your own account."})

        if "role" in attrs or "custom_role" in attrs:
            _validate_role_assignment(actor, role, institution_id, custom_role)
        return attrs


class UserProfileUpdateSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """Explicit allowlist for a user editing their own profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "preferred_language"]
        extra_kwargs = {
            "first_name": {"max_length": 150, "allow_blank": True},
            "last_name": {"max_length": 150, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
        }


class UserCreateSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    # Optional: when omitted the account gets an unusable password and the
    # administrator can issue a reset link. No password is ever generated here.
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "role",
            "custom_role", "institution", "phone", "preferred_language", "password",
        ]

    def validate_password(self, value):
        if not value:
            return value
        user = User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        try:
            password_validation.validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if not actor or not actor.is_authenticated:
            raise serializers.ValidationError("Authentication is required to create users.")
        institution = attrs.get("institution")
        institution_id = _actor_institution(actor, getattr(institution, "id", None))
        custom_role = _resolve_custom_role(actor, attrs.get("custom_role"))
        role = attrs["role"]
        if role == Roles.CUSTOM:
            if custom_role is None:
                raise serializers.ValidationError({
                    "custom_role": "Choose a custom role for this account."
                })
            if not is_platform_admin(actor):
                custom_institution = getattr(custom_role, "institution_id", None)
                if custom_institution is not None and custom_institution != institution_id:
                    raise serializers.ValidationError({
                        "custom_role": "Choose a custom role from this institution."
                    })
            attrs["custom_role"] = custom_role
        else:
            attrs.pop("custom_role", None)
        _validate_role_assignment(actor, role, institution_id, custom_role)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        if not (validated_data.get("username") or "").strip():
            validated_data["username"] = _generate_username(
                validated_data.get("first_name", ""),
                validated_data.get("last_name", ""),
            )
        password = validated_data.pop("password", "")
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.must_change_password = True
        else:
            user.set_unusable_password()
            user.must_change_password = False
        user.save()
        if user.role == Roles.TEACHER and user.institution_id:
            # Administrator-created teachers are approved at creation, unlike
            # public sign-ups which remain inactive until explicitly reviewed.
            teacher = Teacher.objects.create(
                user=user, institution=user.institution, phone=user.phone,
            )
            TeacherApproval.objects.create(
                institution=user.institution, teacher=teacher,
                status="APPROVED", decided_by=self.context["request"].user,
                decided_at=timezone.now(),
                notes="Created directly by an administrator.",
            )
            profile, _ = OnboardingProfile.objects.get_or_create(user=user)
            profile.teacher_approved = True
            profile.mark_complete_if_ready()
            profile.save(update_fields=["teacher_approved", "completed_at", "updated_at"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            # authenticate() rejects inactive users before this serializer can
            # explain why. Verify the credentials directly so a pending teacher
            # gets a useful message, while a wrong password stays generic.
            candidate = User.objects.filter(username=attrs["username"]).first()
            if (candidate and not candidate.is_active
                    and candidate.check_password(attrs["password"])):
                if candidate.role == Roles.TEACHER:
                    raise serializers.ValidationError(
                        "Your teacher account is awaiting school administrator approval."
                    )
                raise serializers.ValidationError("This account has been deactivated.")
            raise serializers.ValidationError(
                "We could not verify those sign-in details. Check your username "
                "and password and try again."
            )
        if not user.is_active:
            if user.role == Roles.TEACHER:
                raise serializers.ValidationError(
                    "Your teacher account is awaiting school administrator approval."
                )
            raise serializers.ValidationError("This account has been deactivated.")
        attrs["user"] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Incorrect password."})
        return attrs

    @transaction.atomic
    def save(self):
        request = self.context["request"]
        user = request.user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        invalidate_user_sessions(user, keep_session_key=request.session.session_key)
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]
        users = User.objects.filter(email__iexact=email, is_active=True)
        configured_base = (getattr(settings, "FRONTEND_BASE_URL", "") or "").rstrip("/")
        request = self.context.get("request")
        base = configured_base
        if not base and request is not None:
            base = request.build_absolute_uri("/").rstrip("/")
        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            path = f"/reset-password/{uid}/{token}/"
            link = f"{base}{path}" if base else path
            user.email_user(
                subject="Reset your KLB Elimu password",
                message=f"Use this link to reset your password:\n\n"
                        f"{link}\n\n"
                        f"If you did not request this, ignore this message.",
            )
        return users.count()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid reset link."})
        token_hash = hash_reset_token(attrs["token"])
        if PasswordResetUse.objects.filter(token_hash=token_hash).exists():
            raise serializers.ValidationError({"token": "This reset link has already been used."})
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "This reset link has expired."})
        attrs["user"] = user
        attrs["token_hash"] = token_hash
        return attrs

    @transaction.atomic
    def save(self):
        user = self.validated_data["user"]
        _, created = PasswordResetUse.objects.get_or_create(
            user=user, token_hash=self.validated_data["token_hash"]
        )
        if not created:
            raise serializers.ValidationError({"token": "This reset link has already been used."})
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        invalidate_user_sessions(user)
        return user


class PublicRegistrationSerializer(serializers.Serializer):
    """Self-service signup for learners, guardians and provisional teachers.

    Administrator roles are deliberately absent. Teacher accounts are created
    inactive until a school administrator approves them.
    """

    PUBLIC_ROLES = {Roles.LEARNER, Roles.GUARDIAN, Roles.TEACHER}

    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=[(r, r.title()) for r in sorted(PUBLIC_ROLES)])
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.filter(is_active=True))
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.CharField(max_length=10, required=False, allow_blank=True)
    relationship_to_learner = serializers.CharField(max_length=50, required=False, allow_blank=True)
    learner_identifier = serializers.CharField(max_length=50, required=False, allow_blank=True)
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    employment_type = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already in use.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exclude(email="").exists():
            raise serializers.ValidationError("That email address is already in use.")
        return value

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_password(self, value):
        user = User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        try:
            password_validation.validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def _resolve_learner(self, identifier, institution):
        """Resolve a guardian's learner code against the selected school."""
        identifier = (identifier or "").strip()
        if not identifier:
            return None
        return (
            Learner.objects.filter(
                institution=institution, admission_number__iexact=identifier
            ).first()
            or Learner.objects.filter(
                institution=institution, assessment_number__iexact=identifier
            ).first()
        )

    def validate(self, attrs):
        role = attrs["role"]
        if role == Roles.LEARNER:
            if not attrs.get("date_of_birth"):
                raise serializers.ValidationError({"date_of_birth": "Learners must provide a date of birth."})
            if not attrs.get("gender"):
                raise serializers.ValidationError({"gender": "Learners must provide a gender."})
        if role == Roles.GUARDIAN:
            if not attrs.get("relationship_to_learner"):
                raise serializers.ValidationError({
                    "relationship_to_learner": "Guardians must state their relationship to the learner."
                })
            identifier = attrs.get("learner_identifier", "")
            if not identifier.strip():
                raise serializers.ValidationError({
                    "learner_identifier": "Enter your learner's admission or assessment number."
                })
            if not self._resolve_learner(identifier, attrs["institution"]):
                raise serializers.ValidationError({
                    "learner_identifier": (
                        "The learner details could not be linked. Check the school and "
                        "learner number or contact the office."
                    )
                })
        if role == Roles.TEACHER and not attrs.get("employment_type"):
            raise serializers.ValidationError({"employment_type": "Teachers must state their employment type."})
        return attrs

    def create(self, validated_data):
        username = (validated_data.pop("username", "") or "").strip()
        if not username:
            username = _generate_username(
                validated_data.get("first_name", ""),
                validated_data.get("last_name", ""),
            )
        validated_data["username"] = username
        role = validated_data.pop("role")
        institution = validated_data.pop("institution")
        date_of_birth = validated_data.pop("date_of_birth", None)
        gender = validated_data.pop("gender", "")
        relationship = validated_data.pop("relationship_to_learner", "")
        learner_identifier = validated_data.pop("learner_identifier", "")
        occupation = validated_data.pop("occupation", "")
        employment_type = validated_data.pop("employment_type", "")
        password = validated_data.pop("password")

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    **validated_data,
                    role=role,
                    institution=institution,
                    is_active=role != Roles.TEACHER,
                )
                user.set_password(password)
                user.must_change_password = False
                user.save()

                if role == Roles.LEARNER:
                    Learner.objects.create(
                        user=user, institution=institution, date_of_birth=date_of_birth,
                        gender=gender, status="ACTIVE", date_admitted=timezone.localdate(),
                    )
                elif role == Roles.GUARDIAN:
                    guardian = Guardian.objects.create(
                        user=user, institution=institution, phone=validated_data.get("phone", ""),
                        occupation=occupation, relationship_to_learner=relationship,
                    )
                    learner = self._resolve_learner(learner_identifier, institution)
                    GuardianLinkRequest.objects.create(
                        institution=institution,
                        guardian=guardian,
                        learner=learner,
                        learner_identifier=learner_identifier.strip(),
                        relationship=relationship,
                        status="PENDING",
                    )
                elif role == Roles.TEACHER:
                    teacher = Teacher.objects.create(
                        user=user, institution=institution, phone=validated_data.get("phone", ""),
                        employment_type=employment_type if employment_type in {"PERMANENT", "CONTRACT", "PART_TIME", "VOLUNTEER"} else "CONTRACT",
                        is_active=False,
                    )
                    TeacherApproval.objects.create(
                        institution=institution, teacher=teacher, status="PENDING"
                    )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "An account with that username or email already exists."
            ) from exc
        return user


class AdminInvitationSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    class Meta:
        model = AdminInvitation
        fields = [
            "id", "email", "role", "custom_role", "institution", "token",
            "expires_at", "accepted_at", "revoked", "created_at",
        ]
        read_only_fields = ["id", "token", "expires_at", "accepted_at", "revoked", "created_at"]

    def validate(self, attrs):
        actor = self.context["request"].user
        role = attrs["role"]
        institution = attrs.get("institution")
        raw_institution_id = getattr(institution, "id", institution)
        if is_institution_admin(actor) and not is_platform_admin(actor):
            if raw_institution_id not in (None, ""):
                try:
                    if int(raw_institution_id) != int(actor.institution_id):
                        raise serializers.ValidationError({
                            "institution": "You can only invite administrators to your own institution."
                        })
                except (TypeError, ValueError):
                    raise serializers.ValidationError({
                        "institution": "You can only invite administrators to your own institution."
                    })
            institution_id = actor.institution_id
        else:
            institution_id = _actor_institution(actor, raw_institution_id)
        custom_role = _resolve_custom_role(actor, attrs.get("custom_role"))
        if role == Roles.CUSTOM:
            if custom_role is None:
                raise serializers.ValidationError({
                    "custom_role": "Choose a custom role for this invitation."
                })
            attrs["custom_role"] = custom_role
            if custom_role.institution_id is not None:
                if institution_id is None:
                    institution = custom_role.institution
                    attrs["institution"] = institution
                    institution_id = institution.id
                elif custom_role.institution_id != institution_id:
                    raise serializers.ValidationError({
                        "custom_role": "Choose a custom role from the invited institution."
                    })
        else:
            attrs.pop("custom_role", None)
            custom_role = None

        if role == Roles.ADMIN and institution_id is None:
            raise serializers.ValidationError({
                "institution": "Administrators must belong to an institution."
            })
        _validate_role_assignment(actor, role, institution_id, custom_role)
        if is_institution_admin(actor) and not is_platform_admin(actor):
            if not actor.institution_id:
                raise serializers.ValidationError("Your account is not attached to an institution.")
            if institution_id is not None and institution_id != actor.institution_id:
                raise serializers.ValidationError({
                    "institution": "You can only invite administrators to your own institution."
                })
        return attrs

    def create(self, validated_data):
        validated_data.update({
            "token": secrets.token_urlsafe(32),
            "expires_at": timezone.now() + timedelta(days=7),
            "invited_by": self.context["request"].user,
        })
        return super().create(validated_data)


class AdminInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_token(self, value):
        invitation = AdminInvitation.objects.filter(token=value).first()
        if not invitation or not invitation.is_usable:
            raise serializers.ValidationError("This invitation is invalid, expired or already used.")
        if User.objects.filter(email__iexact=invitation.email).exclude(email="").exists():
            raise serializers.ValidationError("An account already exists for this invitation.")
        self.invitation = invitation
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already in use.")
        return value

    def validate_password(self, value):
        user = User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        try:
            password_validation.validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        invitation = getattr(self, "invitation", None)
        if invitation and attrs["email"].strip().lower() != invitation.email.strip().lower():
            raise serializers.ValidationError({"email": "Use the email address on the invitation."})
        return attrs

    def save(self):
        attrs = dict(self.validated_data)
        password = attrs.pop("password")
        attrs.pop("token")
        try:
            with transaction.atomic():
                invitation = AdminInvitation.objects.select_for_update().get(pk=self.invitation.pk)
                if not invitation.is_usable:
                    raise serializers.ValidationError(
                        "This invitation is invalid, expired or already used."
                    )
                user = User.objects.create_user(
                    **attrs,
                    role=invitation.role,
                    custom_role=invitation.custom_role if invitation.role == Roles.CUSTOM else None,
                    institution=invitation.institution,
                    is_staff=invitation.role in Roles.ADMIN_ROLES,
                    is_active=True,
                )
                user.set_password(password)
                user.must_change_password = False
                user.save()
                profile, _ = OnboardingProfile.objects.get_or_create(user=user)
                profile.profile_complete = True
                profile.mark_complete_if_ready()
                profile.save(update_fields=["profile_complete", "completed_at", "updated_at"])
                invitation.accepted_at = timezone.now()
                invitation.save(update_fields=["accepted_at"])
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "An account with that username or email already exists."
            ) from exc
        return user


class CustomRoleSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    """Create and edit reusable permission sets."""

    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = CustomRole
        fields = [
            "id", "name", "description", "permissions", "capabilities",
            "institution", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "capabilities", "created_at", "updated_at"]

    def get_capabilities(self, obj):
        return obj.capabilities

    def validate_permissions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Permissions must be a list.")
        unknown = [item for item in value if item not in Capabilities.ALL]
        if unknown:
            raise serializers.ValidationError(
                f"Unknown capabilities: {', '.join(sorted(map(str, unknown)))}."
            )
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        actor = self.context["request"].user
        instance = self.instance
        institution = attrs.get(
            "institution", getattr(instance, "institution", None) if instance else None
        )
        institution_id = _actor_institution(
            actor, getattr(institution, "id", institution)
        )
        if not is_platform_admin(actor):
            if not institution_id or not same_institution(actor, institution_id):
                raise serializers.ValidationError({
                    "institution": "Custom roles belong to your own institution."
                })
            if instance and instance.institution_id != institution_id:
                raise serializers.ValidationError({
                    "institution": "You cannot move a custom role to another institution."
                })

        name = (attrs.get("name", getattr(instance, "name", "")) or "").strip()
        queryset = CustomRole.objects.filter(name__iexact=name, institution_id=institution_id)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({
                "name": "A custom role with this name already exists here."
            })
        attrs["name"] = name
        return attrs

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
