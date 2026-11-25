"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.core.throttling import TutorThrottle
from apps.core.viewsets import InstitutionScopedQuerysetMixin
from apps.tutor.models import TutorConversation, TutorMessage
from apps.tutor.scoping import (
    can_use_tutor,
    may_manage_conversation,
    scoped_conversations,
    validate_learner_choice,
)
from apps.tutor.serializers import (
    AskQuestionSerializer,
    TutorConversationSerializer,
    TutorMessageSerializer,
)
from apps.tutor.service import clean_question, get_provider


class CanUseTutor(BasePermission):
    """Staff and portal users may use the tutor; anonymous users may not."""

    message = "You need a school account to use the learning assistant."

    def has_permission(self, request, view):
        return can_use_tutor(request.user)


class CanManageConversation(BasePermission):
    """A user may only act on conversations that are visible to them."""

    message = "You cannot change this conversation."

    def has_object_permission(self, request, view, obj):
        return may_manage_conversation(request.user, obj)


class TutorConversationViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    """Conversations scoped to the caller; staff see the whole institution."""

    queryset = TutorConversation.objects.select_related("learner", "started_by")
    serializer_class = TutorConversationSerializer
    throttle_classes = [TutorThrottle]
    filterset_fields = ["status", "learner"]
    search_fields = ["reference", "title"]
    write_object_actions = {"update", "partial_update", "destroy", "ask"}

    def get_permissions(self):
        permissions = [IsAuthenticated(), CanUseTutor()]
        if self.action in self.write_object_actions:
            permissions.append(CanManageConversation())
        return permissions

    def get_queryset(self):
        return scoped_conversations(self.request.user, super().get_queryset())

    def perform_create(self, serializer):
        # The actor and learner are resolved server-side so a payload cannot
        # impersonate another user or another school's learner.
        user = self.request.user
        learner = serializer.validated_data.get("learner")
        learner = validate_learner_choice(user, learner)
        kwargs = {"started_by": user}
        if learner is not None:
            kwargs["learner"] = learner
        self._scoped_save(serializer, **kwargs)

    def perform_update(self, serializer):
        # The actor stays unchanged; learner changes are validated by the
        # serializer against the caller's own links.
        self._scoped_save(serializer)

    @action(detail=True, methods=["post"])
    def ask(self, request, pk=None):
        conversation = self.get_object()
        ask_serializer = AskQuestionSerializer(data=request.data)
        ask_serializer.is_valid(raise_exception=True)
        question = clean_question(ask_serializer.validated_data["question"])

        TutorMessage.objects.create(
            institution=conversation.institution,
            conversation=conversation,
            role=TutorMessage.Role.USER,
            body=question,
            created_by=request.user,
        )
        result = get_provider().answer(question, conversation.institution)
        tutor_message = TutorMessage.objects.create(
            institution=conversation.institution,
            conversation=conversation,
            role=TutorMessage.Role.TUTOR,
            body=result["answer"],
            sources=result["sources"],
            suggestions=result["suggestions"],
            created_by=request.user,
        )
        return Response(
            TutorMessageSerializer(tutor_message).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def health(self, request):
        """Report the provider name without exposing any configuration value."""
        return Response({"provider": get_provider().name, "grounded_only": True})


class TutorMessageViewSet(InstitutionScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only message history for conversations the caller can access."""

    queryset = TutorMessage.objects.select_related("conversation")
    serializer_class = TutorMessageSerializer
    filterset_fields = ["conversation", "role"]
    search_fields = ["body", "reference"]

    def get_permissions(self):
        return [IsAuthenticated(), CanUseTutor()]

    def get_queryset(self):
        conversations = scoped_conversations(
            self.request.user, TutorConversation.objects.all()
        )
        return super().get_queryset().filter(conversation__in=conversations)
