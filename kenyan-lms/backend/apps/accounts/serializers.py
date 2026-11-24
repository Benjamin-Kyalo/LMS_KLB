"""Serializers for authentication and user management."""
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, password_validation
from django.db import IntegrityError, transaction
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

from apps.accounts.models import AdminInvitation, User
from apps.core.constants import Roles
from apps.core.permissions import can_assign_role, is_institution_admin, is_platform_admin
from apps.guardians.models import Guardian
from apps.institutions.models import Institution
from apps.learners.models import Learner
from apps.teachers.models import Teacher


class UserSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_code = serializers.CharField(source="institution.code", read_only=True)
    institution_logo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "full_name",
            "role", "institution", "institution_name", "institution_code",
            "institution_logo", "phone", "preferred_language", "is_active",
            "must_change_password", "date_joined", "last_login",
        ]
        read_only_fields = [
            "id", "date_joined", "last_login", "full_name", "institution_name",
            "institution_code", "institution_logo",
        ]

    def get_institution_logo(self, obj):
        if not obj.institution_id or not obj.institution.logo:
            return None
        request = self.context.get("request")
        url = obj.institution.logo.url
        return request.build_absolute_uri(url) if request else url

    def validate(self, attrs):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if not actor or not actor.is_authenticated:
            return attrs

        role = attrs.get("role", getattr(self.instance, "role", None))
        institution = attrs.get("institution", getattr(self.instance, "institution", None))
        institution_id = getattr(institution, "id", institution)
        if is_institution_admin(actor) and not is_platform_admin(actor):
            institution_id = actor.institution_id

        if self.instance and self.instance.pk == actor.pk:
            if "role" in attrs and role != actor.role:
                raise serializers.ValidationError({"role": "You cannot change your own role."})
            if "is_active" in attrs and not attrs["is_active"]:
                raise serializers.ValidationError({"is_active": "You cannot deactivate your own account."})
            if "institution" in attrs and not is_platform_admin(actor):
                raise serializers.ValidationError({"institution": "You cannot move your own account."})

        if "role" in attrs and not can_assign_role(actor, role, institution_id):
            raise serializers.ValidationError({"role": "You are not allowed to assign this role."})
        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    # Optional: when omitted the account gets an unusable password and the
    # administrator can issue a reset link. No password is ever generated here.
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "role",
            "institution", "phone", "preferred_language", "password",
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
        institution_id = getattr(institution, "id", None)
        # School admins are scoped by the viewset; their payload cannot choose
        # an institution, so validate against the institution they actually own.
        if is_institution_admin(actor) and not is_platform_admin(actor):
            institution_id = actor.institution_id
        if not can_assign_role(actor, attrs["role"], institution_id):
            raise serializers.ValidationError({"role": "You are not allowed to assign this role."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.must_change_password = True
        else:
            user.set_unusable_password()
            user.must_change_password = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
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

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]
        users = User.objects.filter(email__iexact=email, is_active=True)
        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            user.email_user(
                subject="Reset your KLB LMS password",
                message=f"Use this link to reset your password:\n\n"
                        f"/reset-password/{uid}/{token}/\n\n"
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
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "This reset link has expired."})
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return user


class PublicRegistrationSerializer(serializers.Serializer):
    """Self-service signup for learners, guardians and provisional teachers.

    Administrator roles are deliberately absent. Teacher accounts are created
    inactive until a school administrator approves them.
    """

    PUBLIC_ROLES = {Roles.LEARNER, Roles.GUARDIAN, Roles.TEACHER}

    username = serializers.CharField(max_length=150)
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

    def validate(self, attrs):
        role = attrs["role"]
        if role == Roles.LEARNER:
            if not attrs.get("date_of_birth"):
                raise serializers.ValidationError({"date_of_birth": "Learners must provide a date of birth."})
            if not attrs.get("gender"):
                raise serializers.ValidationError({"gender": "Learners must provide a gender."})
        if role == Roles.GUARDIAN and not attrs.get("relationship_to_learner"):
            raise serializers.ValidationError({
                "relationship_to_learner": "Guardians must state their relationship to the learner."
            })
        if role == Roles.TEACHER and not attrs.get("employment_type"):
            raise serializers.ValidationError({"employment_type": "Teachers must state their employment type."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop("role")
        institution = validated_data.pop("institution")
        date_of_birth = validated_data.pop("date_of_birth", None)
        gender = validated_data.pop("gender", "")
        relationship = validated_data.pop("relationship_to_learner", "")
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
                    Guardian.objects.create(
                        user=user, institution=institution, phone=validated_data.get("phone", ""),
                        occupation=occupation, relationship_to_learner=relationship,
                    )
                elif role == Roles.TEACHER:
                    Teacher.objects.create(
                        user=user, institution=institution, phone=validated_data.get("phone", ""),
                        employment_type=employment_type if employment_type in {"PERMANENT", "CONTRACT", "PART_TIME", "VOLUNTEER"} else "CONTRACT",
                        is_active=False,
                    )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "An account with that username or email already exists."
            ) from exc
        return user


class AdminInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminInvitation
        fields = [
            "id", "email", "role", "institution", "token", "expires_at",
            "accepted_at", "revoked", "created_at",
        ]
        read_only_fields = ["id", "token", "expires_at", "accepted_at", "revoked", "created_at"]

    def _actor_institution_id(self, actor, raw_value):
        if is_institution_admin(actor) and not is_platform_admin(actor):
            return actor.institution_id
        try:
            return int(raw_value) if raw_value not in (None, "") else None
        except (TypeError, ValueError):
            return raw_value

    def validate_role(self, value):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        institution = self._actor_institution_id(actor, self.initial_data.get("institution"))
        if not can_assign_role(actor, value, institution):
            raise serializers.ValidationError("You are not allowed to invite this administrator role.")
        return value

    def validate(self, attrs):
        actor = self.context["request"].user
        role = attrs["role"]
        institution = attrs.get("institution")
        if role in Roles.INSTITUTION_ADMIN_ROLES and institution is None:
            raise serializers.ValidationError({
                "institution": "School and institution administrators must belong to an institution."
            })
        if is_institution_admin(actor) and not is_platform_admin(actor):
            if not actor.institution_id:
                raise serializers.ValidationError("Your account is not attached to an institution.")
            if institution and institution.id != actor.institution_id:
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
                    institution=invitation.institution,
                    is_staff=True,
                    is_active=True,
                )
                user.set_password(password)
                user.must_change_password = False
                user.save()
                invitation.accepted_at = timezone.now()
                invitation.save(update_fields=["accepted_at"])
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "An account with that username or email already exists."
            ) from exc
        return user
