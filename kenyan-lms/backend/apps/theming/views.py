"""Public active-theme endpoint and administrator palette management."""
from copy import deepcopy
from uuid import uuid4

from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.concurrency import ConflictAwareMixin, conflict_response
from apps.core.models import AuditLog
from apps.core.permissions import IsInstitutionAdmin, IsPlatformAdmin
from apps.theming.catalogue import DEFAULT_ACTIVE_SLUG
from apps.theming.models import SiteContent, ThemePalette
from apps.theming.serializers import SiteContentSerializer, ThemePaletteSerializer
from apps.theming.site_content import (
    DEFAULT_SITE_CONTENT, PUBLIC_SITE_KEY, deep_merge, normalise_site_content,
    public_site_content,
)
from apps.theming.uploads import validate_site_image


def active_palette():
    """Return the selected palette, with a deterministic fallback."""
    palette = ThemePalette.objects.filter(is_active=True).first()
    if palette is None:
        palette = ThemePalette.objects.filter(slug=DEFAULT_ACTIVE_SLUG).first()
    if palette is None:
        palette = ThemePalette.objects.order_by("name").first()
    return palette


def _audit(request, action, palette, details):
    user = request.user if request.user.is_authenticated else None
    AuditLog.objects.create(
        institution=user.institution if user and user.institution_id else None,
        user=user,
        action=action,
        entity_type="ThemePalette",
        entity_id=str(palette.pk),
        details=details,
        ip_address=request.META.get("REMOTE_ADDR") or None,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def active_theme(request):
    """Read the active palette. Public pages need it before sign-in."""
    palette = active_palette()
    if palette is None:
        return Response(
            {"detail": "No theme palette has been configured."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ThemePaletteSerializer(palette).data)


def _site_content_object(create=True):
    """Read the editable content row without inserting one on public reads."""
    if create:
        record, _ = SiteContent.objects.get_or_create(key=PUBLIC_SITE_KEY)
        return record
    return SiteContent.objects.filter(key=PUBLIC_SITE_KEY).first()


class SiteContentView(APIView):
    """Public wording, navigation and section styles, editable by administrators."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        # School and institution admins manage shared public appearance alongside
        # photographs. Wording and styles are still validated against one schema.
        return [IsAuthenticated(), IsInstitutionAdmin()]

    def get(self, request):
        record = _site_content_object(create=False)
        return Response(public_site_content(record.content if record else None))

    @transaction.atomic
    def patch(self, request):
        record = _site_content_object()
        expected = request.headers.get("If-Match")
        if expected:
            actual = record.updated_at.isoformat()
            if expected.strip().strip('"') != actual:
                return conflict_response("This record changed since you loaded it.", {
                    "id": record.pk,
                    "updated_at": actual,
                    "data": public_site_content(record.content),
                })
        payload = request.data.get("content", request.data)
        # A PATCH may contain only the sections being changed. Merge onto the
        # saved document first so omitted wording and styles keep their values.
        merged = deep_merge(record.content, payload) if isinstance(payload, dict) else payload
        serializer = SiteContentSerializer(
            record, data={"content": merged}, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(updated_by=request.user)
            sections = sorted(payload.keys()) if isinstance(payload, dict) else []
            AuditLog.objects.create(
                institution=request.user.institution if request.user.institution_id else None,
                user=request.user,
                action="site_content.updated",
                entity_type="SiteContent",
                entity_id=str(record.pk),
                details={"sections": sections},
                ip_address=request.META.get("REMOTE_ADDR") or None,
            )
        record.refresh_from_db()
        return Response(public_site_content(record.content))


# The admin Photos section writes only to these approved content paths. A slot
# can never name an arbitrary field, so an upload cannot change wording or links.
SITE_IMAGE_SLOTS = {
    "hero": ("hero", "imageSrc"),
    "workspace-learning": ("workspaces", "cards", 0, "image"),
    "workspace-school": ("workspaces", "cards", 1, "image"),
    "workspace-publishing": ("workspaces", "cards", 2, "image"),
    "insights": ("insights", "imageSrc"),
    "spotlight": ("spotlight", "imageSrc"),
    "login": ("auth", "login", "storyImageSrc"),
    "register": ("auth", "register", "storyImageSrc"),
    "tutor": ("portal", "tutorImageSrc"),
}


def _set_content_path(content, parts, value):
    current = content
    for part in parts[:-1]:
        if isinstance(part, int):
            if not isinstance(current, list) or len(current) <= part:
                raise ValidationError({"slot": "This photo slot is unavailable."})
            current = current[part]
        else:
            if not isinstance(current, dict):
                raise ValidationError({"slot": "This photo slot is unavailable."})
            current = current.setdefault(part, {})
    last = parts[-1]
    if isinstance(last, int):
        if not isinstance(current, list) or len(current) <= last:
            raise ValidationError({"slot": "This photo slot is unavailable."})
    elif not isinstance(current, dict):
        raise ValidationError({"slot": "This photo slot is unavailable."})
    current[last] = value


def _default_content_path(parts):
    """Read the shipped value for an approved photo slot."""
    current = DEFAULT_SITE_CONTENT
    for part in parts:
        if isinstance(part, int):
            if not isinstance(current, list) or len(current) <= part:
                raise ValidationError({"slot": "This photo slot has no default."})
        elif not isinstance(current, dict) or part not in current:
            raise ValidationError({"slot": "This photo slot has no default."})
        current = current[part]
    return current if isinstance(current, str) else ""


def _managed_image_path(value):
    """Return the storage path for a managed upload, or None for shipped art."""
    if not isinstance(value, str):
        return None
    marker = "/site-content/"
    if marker not in value:
        return None
    return "site-content/" + value.split(marker, 1)[1].split("?", 1)[0]


def _discard_managed_image(value):
    path = _managed_image_path(value)
    if path and default_storage.exists(path):
        default_storage.delete(path)


def _current_content_path(content, parts):
    current = content
    for part in parts:
        if isinstance(part, int):
            if not isinstance(current, list) or len(current) <= part:
                return ""
            current = current[part]
        elif isinstance(current, dict):
            current = current.get(part, {})
        else:
            return ""
    return current if isinstance(current, str) else ""


def _write_content_path(request, slot, value, audit_action):
    """Remove or reset one photo slot without touching any other content."""
    parts = SITE_IMAGE_SLOTS[slot]
    with transaction.atomic():
        record = _site_content_object()
        content = deepcopy(record.content)
        previous = _current_content_path(content, parts)
        _set_content_path(content, parts, value)
        normalised = normalise_site_content(content)
        locked = SiteContent.objects.select_for_update().get(pk=record.pk)
        locked.content = normalised
        locked.updated_by = request.user
        locked.save()
        AuditLog.objects.create(
            institution=request.user.institution if request.user.institution_id else None,
            user=request.user,
            action=audit_action,
            entity_type="SiteContent",
            entity_id=str(locked.pk),
            details={"slot": slot},
            ip_address=request.META.get("REMOTE_ADDR") or None,
        )
    # Only remove the superseded upload after the content change has committed.
    if previous != value:
        _discard_managed_image(previous)
    return Response(
        {"slot": slot, "imageSrc": value, "content": public_site_content(normalised)}
    )


class SiteImageUploadBase(APIView):
    """Shared upload, validation, publishing and audit logic."""

    # Photos are site-wide, but school and institution admins may manage them.
    # Wording and section styles use the same administrator rule in SiteContentView.
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]
    parser_classes = [MultiPartParser]

    def publish(self, request, slot, audit_action):
        upload = request.FILES.get("image") or request.FILES.get("file")
        extension = validate_site_image(upload)
        stored_name = f"site-content/{slot}/{slot}-{uuid4().hex}{extension}"

        path = None
        try:
            with transaction.atomic():
                path = default_storage.save(stored_name, upload)
                record = _site_content_object()
                content = deepcopy(record.content)
                previous = _current_content_path(content, SITE_IMAGE_SLOTS[slot])
                image_src = default_storage.url(path)
                _set_content_path(content, SITE_IMAGE_SLOTS[slot], image_src)
                normalised = normalise_site_content(content)

                locked = SiteContent.objects.select_for_update().get(pk=record.pk)
                locked.content = normalised
                locked.updated_by = request.user
                locked.save()
                AuditLog.objects.create(
                    institution=request.user.institution if request.user.institution_id else None,
                    user=request.user,
                    action=audit_action,
                    entity_type="SiteContent",
                    entity_id=str(locked.pk),
                    details={"slot": slot, "path": path},
                    ip_address=request.META.get("REMOTE_ADDR") or None,
                )
        except Exception:
            if path and default_storage.exists(path):
                default_storage.delete(path)
            raise
        if previous != image_src:
            _discard_managed_image(previous)
        return Response(
            {
                "slot": slot,
                "imageSrc": image_src,
                "content": public_site_content(normalised),
            },
            status=status.HTTP_201_CREATED,
        )


class SiteImageView(SiteImageUploadBase):
    """Upload and publish any approved public-site photo slot."""

    def post(self, request):
        slot = request.data.get("slot")
        if slot not in SITE_IMAGE_SLOTS:
            raise ValidationError({"slot": "Choose a supported photo slot."})
        return self.publish(request, slot, "site_content.image_uploaded")


class SiteImageSlotView(SiteImageUploadBase):
    """Remove the uploaded photo from one approved slot."""

    def delete(self, request, slot):
        if slot not in SITE_IMAGE_SLOTS:
            raise ValidationError({"slot": "Choose a supported photo slot."})
        return _write_content_path(
            request, slot, "", "site_content.image_removed"
        )


class SiteImageResetView(SiteImageUploadBase):
    """Restore the shipped photo for one approved slot."""

    def post(self, request, slot):
        if slot not in SITE_IMAGE_SLOTS:
            raise ValidationError({"slot": "Choose a supported photo slot."})
        return _write_content_path(
            request, slot,
            _default_content_path(SITE_IMAGE_SLOTS[slot]),
            "site_content.image_reset",
        )


class SiteHeroImageView(SiteImageUploadBase):
    """Legacy hero-only endpoint, kept for older admin clients."""

    def post(self, request):
        return self.publish(request, "hero", "site_content.hero_image_uploaded")


class ThemePaletteViewSet(ConflictAwareMixin, viewsets.ModelViewSet):
    """Global palette catalogue. Platform and institution admins may change it."""

    queryset = ThemePalette.objects.all()
    serializer_class = ThemePaletteSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]
    filterset_fields = ["is_active", "is_builtin"]
    search_fields = ["name", "description", "source_label", "slug"]
    ordering = ["name", "id"]

    def perform_create(self, serializer):
        with transaction.atomic():
            palette = serializer.save(created_by=self.request.user)
            _audit(self.request, "theme.palette.created", palette, {"name": palette.name})

    def perform_update(self, serializer):
        with transaction.atomic():
            palette = serializer.save()
            _audit(self.request, "theme.palette.updated", palette, {"name": palette.name})

    def destroy(self, request, *args, **kwargs):
        palette = self.get_object()
        if palette.is_builtin:
            raise ValidationError({"detail": "Built-in palettes cannot be deleted."})
        if palette.is_active:
            raise ValidationError({"detail": "Activate another palette before deleting this one."})
        with transaction.atomic():
            _audit(request, "theme.palette.deleted", palette, {"name": palette.name})
            return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """Make one palette active for the whole platform atomically."""
        palette = self.get_object()
        with transaction.atomic():
            ThemePalette.objects.select_for_update().filter(is_active=True).exclude(
                pk=palette.pk
            ).update(is_active=False)
            locked = ThemePalette.objects.select_for_update().get(pk=palette.pk)
            if not locked.is_active:
                locked.is_active = True
                locked.save(update_fields=["is_active", "updated_at"])
            palette.refresh_from_db()
            _audit(request, "theme.palette.activated", palette, {"name": palette.name})
        return Response(ThemePaletteSerializer(palette).data)
