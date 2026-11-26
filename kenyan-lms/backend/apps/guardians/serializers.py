"""Guardian serializers."""
import re

from django.contrib.auth import get_user_model
from django.db import transaction
from apps.core.audit import record_change, snapshot
from apps.core.serializers import InstitutionCodeMixin
from rest_framework import serializers

from apps.core.constants import Roles
from apps.guardians.models import Guardian

User = get_user_model()


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


class GuardianSerializer(InstitutionCodeMixin, serializers.ModelSerializer):
    guardian_name = serializers.CharField(source="user.full_name", read_only=True)
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    institution_code = serializers.CharField(source="institution.code", read_only=True)
    learner_names = serializers.SerializerMethodField()
    learner_ids = serializers.SerializerMethodField()

    def get_learner_names(self, obj):
        return [link.learner.user.full_name for link in obj.learner_links.select_related("learner__user").all()]

    def get_learner_ids(self, obj):
        return [link.learner_id for link in obj.learner_links.all()]

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = instance.user
        identity_fields = ("username", "first_name", "last_name", "email")
        before = snapshot(instance, {field: getattr(user, field) for field in identity_fields})
        user_data = validated_data.pop("user", {})
        for field in identity_fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        if user_data:
            user.save()
        updated = super().update(instance, validated_data)
        after = snapshot(instance, {field: getattr(user, field) for field in identity_fields})
        record_change(
            getattr(request, "user", None), instance, before, after,
            action="guardian.updated", request=request,
        )
        return updated

    class Meta:
        model = Guardian
        fields = "__all__"


class GuardianCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    relationship_to_learner = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        # No password is invented or displayed; use the password reset flow.
        username = (validated_data.get("username") or "").strip()
        if not username:
            username = _generate_username(
                validated_data.get("first_name", ""),
                validated_data.get("last_name", ""),
            )
        user = User.objects.create_user(
            username=username,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email", ""),
            role=Roles.GUARDIAN,
            institution=request.user.institution,
            must_change_password=False,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        return Guardian.objects.create(
            user=user,
            institution=request.user.institution,
            phone=validated_data.get("phone", ""),
            relationship_to_learner=validated_data.get("relationship_to_learner", ""),
        )
