"""Digital publishing API endpoints."""
import os
from urllib.parse import urlparse

from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import (
    Chapter, ContentAccess, ContentResource, DigitalTextbook, EmbedProvider,
    Exercise, ExerciseAttempt, Publisher, ResourceCollection,
)
from apps.content.serializers import (
    ChapterDetailSerializer, ChapterSerializer, ContentAccessSerializer,
    ContentResourcePortalSerializer, ContentResourcePublicSerializer,
    ContentResourceSerializer, DigitalTextbookSerializer, EmbedProviderSerializer,
    ExerciseAttemptSerializer, ExerciseSerializer, PublisherSerializer,
    PublicTextbookSerializer, ResourceCollectionSerializer, TextbookDetailSerializer,
)
from apps.core.constants import (
    ContentStatus, ResourceAccessScope, ResourceDelivery, Roles,
)
from apps.core.permissions import (
    IsContentCurator, is_content_curator, is_institution_admin, is_platform_admin,
    is_staff_user,
)
from apps.core.viewsets import AdminWriteMixin, ContentWriteMixin, InstitutionScopedQuerysetMixin
from apps.curriculum.models import EducationLevel, LearningArea
from apps.institutions.models import SchoolClass, Subject


class CanWriteResource(BasePermission):
    """Curators manage the shared catalogue; school admins manage school copies."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and (is_content_curator(user) or is_institution_admin(user))
        )


class PublishActionMixin:
    """Small reusable action for models with a status field."""

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        obj = self.get_object()
        obj.status = ContentStatus.PUBLISHED
        obj.published_at = timezone.now()
        obj.save()
        return Response({"detail": "Published.", "id": obj.pk})


class PublisherInfoViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    search_fields = ["name"]


class DigitalTextbookViewSet(PublishActionMixin, viewsets.ModelViewSet):
    queryset = DigitalTextbook.objects.select_related("publisher", "subject", "education_level")
    serializer_class = DigitalTextbookSerializer
    filterset_fields = ["status", "subject", "education_level", "publisher"]
    search_fields = ["title", "isbn", "description"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TextbookDetailSerializer
        return DigitalTextbookSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "publish"}:
            return [IsAuthenticated(), IsContentCurator()]
        return super().get_permissions()


class ChapterViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Chapter.objects.select_related("textbook")
    serializer_class = ChapterSerializer
    filterset_fields = ["textbook"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChapterDetailSerializer
        return ChapterSerializer


class ResourceCollectionViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = ResourceCollection.objects.all()
    serializer_class = ResourceCollectionSerializer
    filterset_fields = ["name"]
    search_fields = ["name", "description"]


class EmbedProviderViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = EmbedProvider.objects.all()
    serializer_class = EmbedProviderSerializer
    filterset_fields = ["kind", "is_active"]
    search_fields = ["name", "host"]


def _published_queryset():
    now = timezone.now()
    return ContentResource.objects.filter(
        status=ContentStatus.PUBLISHED,
    ).filter(Q(published_at__isnull=True) | Q(published_at__lte=now))


def _portal_class_ids(user):
    """Classes whose material a user may open. Never grants cross-school access."""
    if not user.is_authenticated or not user.institution_id:
        return set()
    if user.role == Roles.LEARNER:
        learner = getattr(user, "learner_profile", None)
        return {learner.class_room_id} if learner and learner.class_room_id else set()
    if user.role == Roles.GUARDIAN:
        guardian = getattr(user, "guardian_profile", None)
        if not guardian:
            return set()
        from apps.learners.models import Learner
        return set(Learner.objects.filter(
            institution_id=user.institution_id,
            guardian_links__guardian=guardian,
            guardian_links__is_verified=True,
        ).values_list("class_room_id", flat=True).distinct())
    if is_institution_admin(user):
        return set(SchoolClass.objects.filter(
            institution_id=user.institution_id,
        ).values_list("id", flat=True))
    if user.role == Roles.TEACHER:
        teacher = getattr(user, "teacher_profile", None)
        if not teacher:
            return set()
        return set(teacher.class_assignments.filter(
            institution_id=user.institution_id,
        ).values_list("school_class_id", flat=True).distinct())
    return set()


def portal_visible_resources(user):
    """Published public, institution and verified class-scoped resources."""
    if not user.is_authenticated or not user.institution_id:
        return ContentResource.objects.none()
    visible = Q(access_scope=ResourceAccessScope.PUBLIC)
    visible |= Q(access_scope=ResourceAccessScope.INSTITUTION, institution_id=user.institution_id)
    class_ids = _portal_class_ids(user)
    if class_ids:
        visible |= Q(
            access_scope=ResourceAccessScope.CLASS,
            institution_id=user.institution_id,
            school_class_id__in=class_ids,
        )
    return _published_queryset().filter(visible).distinct()


def _is_resource_manager(user):
    """Roles that keep the full administrative resource view."""
    return is_content_curator(user) or is_institution_admin(user)


def _can_download(user, resource):
    if not resource.file:
        return False
    is_public = (
        resource.status == ContentStatus.PUBLISHED
        and resource.access_scope == ResourceAccessScope.PUBLIC
    )
    if not user or not user.is_authenticated:
        return is_public
    if is_platform_admin(user) or is_content_curator(user):
        return True
    if is_institution_admin(user) and resource.institution_id == user.institution_id:
        return True
    if is_public:
        return True
    if not user.institution_id or resource.institution_id != user.institution_id:
        return False
    if resource.access_scope == ResourceAccessScope.INSTITUTION:
        return resource.status == ContentStatus.PUBLISHED
    if resource.access_scope == ResourceAccessScope.CLASS:
        return (
            resource.status == ContentStatus.PUBLISHED
            and resource.school_class_id in _portal_class_ids(user)
        )
    return False


class ContentResourceViewSet(PublishActionMixin, ContentWriteMixin, viewsets.ModelViewSet):
    queryset = ContentResource.objects.select_related(
        "chapter", "textbook", "institution", "education_level", "learning_area",
        "subject", "school_class", "collection", "embed_provider",
    )
    serializer_class = ContentResourceSerializer
    filterset_fields = [
        "chapter", "textbook", "institution", "resource_type", "delivery", "status",
        "access_scope", "offline_available", "education_level", "learning_area",
        "subject", "school_class", "collection", "embed_provider",
    ]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "published_at", "size_kb", "created_at"]
    ordering = ["title"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        write_action = self.action in {"update", "partial_update", "destroy", "publish"}
        if write_action and user.is_authenticated and not is_content_curator(user):
            if not user.institution_id:
                return queryset.none()
            return queryset.filter(institution_id=user.institution_id)
        if (
            self.action in {"list", "retrieve"}
            and user.is_authenticated
            and not _is_resource_manager(user)
        ):
            return portal_visible_resources(user).select_related(
                "chapter", "textbook", "institution", "education_level", "learning_area",
                "subject", "school_class", "collection", "embed_provider",
            )
        return queryset

    def get_serializer_class(self):
        user = self.request.user
        if (
            self.action in {"list", "retrieve"}
            and user.is_authenticated
            and not _is_resource_manager(user)
        ):
            return ContentResourcePortalSerializer
        return ContentResourceSerializer

    def get_permissions(self):
        if self.action == "download":
            return [AllowAny()]
        if self.action in {"create", "update", "partial_update", "destroy", "publish"}:
            return [IsAuthenticated(), CanWriteResource()]
        return [IsAuthenticated()]

    def _save_scoped(self, serializer, **kwargs):
        user = self.request.user
        # School staff cannot move a resource into another school by editing it.
        if user.is_authenticated and not is_platform_admin(user) and user.institution_id:
            kwargs["institution"] = user.institution
        serializer.save(**kwargs)

    def perform_create(self, serializer):
        self._save_scoped(serializer)

    def perform_update(self, serializer):
        self._save_scoped(serializer)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        resource = get_object_or_404(ContentResource.objects.select_related("collection"), pk=pk)
        if not _can_download(request.user, resource):
            return Response(
                {"detail": "This file is not shared with your account."},
                status=403,
            )
        filename = os.path.basename(urlparse(resource.file.name).path) or "resource"
        return FileResponse(resource.file.open("rb"), as_attachment=True, filename=filename)


class ResourceFacetsView(APIView):
    """Public taxonomy plus optional school taxonomy for signed-in readers."""

    permission_classes = [AllowAny]

    def get(self, request):
        levels = EducationLevel.objects.filter(
            framework__is_active=True,
        ).select_related("framework").prefetch_related("learning_areas").order_by("framework", "sequence", "name")
        areas = LearningArea.objects.filter(
            level__framework__is_active=True,
        ).select_related("level").order_by("level", "sequence", "name")
        data = {
            "levels": [{
                "id": level.id,
                "name": level.name,
                "code": level.code,
                "learning_areas": [
                    {"id": area.id, "name": area.name, "code": area.code}
                    for area in level.learning_areas.all()
                ],
            } for level in levels],
            "learning_areas": [
                {"id": area.id, "name": area.name, "level": area.level_id}
                for area in areas
            ],
            "collections": [
                {"id": item.id, "name": item.name, "slug": item.slug}
                for item in ResourceCollection.objects.order_by("name")
            ],
            "types": [
                {"value": value, "label": label}
                for value, label in ContentResource._meta.get_field("resource_type").choices
            ],
        }
        user = request.user
        if user.is_authenticated and user.institution_id:
            data["subjects"] = [
                {"id": item.id, "name": item.name}
                for item in Subject.objects.filter(institution_id=user.institution_id, is_active=True)
            ]
            data["classes"] = [
                {"id": item.id, "name": item.name, "stream": item.stream}
                for item in SchoolClass.objects.filter(institution_id=user.institution_id)
            ]
        return Response(data)


class _ResourceCatalogueView(ListAPIView):
    search_fields = ["title", "description"]
    ordering_fields = ["title", "published_at", "size_kb"]
    ordering = ["title"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        keyword = self.request.query_params.get("keyword") or self.request.query_params.get("q")
        if keyword:
            queryset = queryset.filter(
                Q(keywords__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
            )
        return queryset


class PublicResourceCatalogueView(_ResourceCatalogueView):
    """Anonymous, published, public-only resource discovery."""

    permission_classes = [AllowAny]
    serializer_class = ContentResourcePublicSerializer
    filterset_fields = [
        "resource_type", "delivery", "education_level", "learning_area",
        "collection", "offline_available",
    ]

    def get_queryset(self):
        return _published_queryset().filter(access_scope=ResourceAccessScope.PUBLIC).select_related(
            "education_level", "learning_area", "collection",
        )


class PublicTextbookCatalogueView(ListAPIView):
    """Anonymous book catalogue preview. Licence checks stay in the portal."""

    permission_classes = [AllowAny]
    serializer_class = PublicTextbookSerializer
    filterset_fields = ["subject", "education_level", "publisher"]
    search_fields = ["title", "subtitle", "description", "isbn"]
    ordering_fields = ["title", "published_at"]
    ordering = ["title"]

    def get_queryset(self):
        now = timezone.now()
        return DigitalTextbook.objects.filter(
            status=ContentStatus.PUBLISHED,
            license_type__in=["OPEN", "INSTITUTION", "PER_LEARNER"],
        ).filter(
            Q(published_at__isnull=True) | Q(published_at__lte=now)
        ).select_related("publisher", "subject", "education_level")

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        keyword = self.request.query_params.get("keyword") or self.request.query_params.get("q")
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(subtitle__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(isbn__icontains=keyword)
            )
        return queryset


class PortalResourceCatalogueView(_ResourceCatalogueView):
    """Authenticated resources scoped to the reader's school, class or subjects."""

    permission_classes = [IsAuthenticated]
    serializer_class = ContentResourcePortalSerializer
    document_only = False
    filterset_fields = [
        "resource_type", "delivery", "access_scope", "education_level", "learning_area",
        "collection", "subject", "school_class", "offline_available",
    ]

    def get_queryset(self):
        queryset = portal_visible_resources(self.request.user).select_related(
            "education_level", "learning_area", "collection", "subject", "school_class",
        )
        if self.document_only:
            queryset = queryset.filter(resource_type__in=["PDF", "LINK"])
        return queryset


class PortalDocumentCatalogueView(PortalResourceCatalogueView):
    document_only = True


class ExerciseViewSet(ContentWriteMixin, viewsets.ModelViewSet):
    queryset = Exercise.objects.select_related("chapter")
    serializer_class = ExerciseSerializer
    filterset_fields = ["chapter"]


def _is_staff_user(user):
    return is_staff_user(user)


class ExerciseAttemptViewSet(InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ExerciseAttemptSerializer
    filterset_fields = ["exercise", "learner"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not _is_staff_user(user):
            return queryset.filter(learner__user=user)
        return queryset

    def _own_learner(self, user):
        learner = getattr(user, "learner_profile", None)
        if learner is None:
            raise ValidationError("Your account is not linked to a learner profile.")
        return learner

    def perform_create(self, serializer):
        user = self.request.user
        if _is_staff_user(user):
            learner = serializer.validated_data.get("learner")
            if learner is None:
                raise ValidationError({"learner": "This field is required for staff."})
            serializer.save(institution=learner.institution)
        else:
            learner = self._own_learner(user)
            serializer.save(institution=learner.institution, learner=learner)

    def perform_update(self, serializer):
        user = self.request.user
        if _is_staff_user(user):
            super().perform_update(serializer)
        else:
            learner = self._own_learner(user)
            serializer.save(
                institution=learner.institution,
                learner=learner,
                exercise=serializer.instance.exercise,
            )


class ContentAccessViewSet(AdminWriteMixin, InstitutionScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ContentAccessSerializer
    filterset_fields = ["textbook", "is_active"]


class AvailableTextbookViewSet(viewsets.ReadOnlyModelViewSet):
    """Textbooks the logged-in institution is licensed to use."""

    serializer_class = DigitalTextbookSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_platform_user:
            return DigitalTextbook.objects.filter(status="PUBLISHED")
        if not user.institution_id:
            return DigitalTextbook.objects.none()
        return DigitalTextbook.objects.filter(
            status="PUBLISHED",
            access_grants__institution_id=user.institution_id,
            access_grants__is_active=True,
        ).distinct()
