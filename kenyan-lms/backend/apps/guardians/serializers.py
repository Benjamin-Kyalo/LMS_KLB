"""Guardian serializers."""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.core.constants import Roles
from apps.guardians.models import Guardian

User = get_user_model()


class GuardianSerializer(serializers.ModelSerializer):
    guardian_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Guardian
        fields = "__all__"


class GuardianCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    relationship_to_learner = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        # No password is invented or displayed; use the password reset flow.
        user = User.objects.create_user(
            username=validated_data["username"],
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
