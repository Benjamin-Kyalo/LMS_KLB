"""Content serializers.

Public and portal resources use explicit allowlists. The admin serializer is
the only place that accepts file paths, institution IDs and draft status.
"""
import os
from urllib.parse import urlparse

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from apps.content.models import (
    HOSTS_BY_KIND, Chapter, ContentAccess, ContentResource, DigitalTextbook,
    EmbedProvider, Exercise, ExerciseAttempt, Publisher, ResourceCollection,
    normalise_host,
)
from apps.core.constants import (
    ContentStatus, EmbedProviderKind, ResourceAccessScope, ResourceDelivery, Roles,
)
from apps.core.permissions import is_staff_user, same_institution

ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".txt",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp3", ".wav", ".ogg", ".mp4", ".webm",
}
ALLOWED_UPLOAD_MIME = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv", "image/png", "image/jpeg", "image/gif", "image/webp",
    "audio/mpeg", "audio/wav", "audio/ogg", "video/mp4", "video/webm",
}


def _is_https(value):
    try:
        return urlparse(str(value or "")).scheme == "https"
    except ValueError:
        return False


def _max_upload_bytes():
    return getattr(settings, "CONTENT_RESOURCE_MAX_UPLOAD_BYTES", 5 * 1024 * 1024)


# Content sniffing is based on the file's extension and its actual bytes. The
# client-supplied content_type is never used to decide what a file really is.
_PDF_SIGNATURE = b"%PDF-"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_OLE2_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_MP3_SIGNATURES = (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xfa", b"\xff\xf4", b"\xff\xfc")
_EBML_SIGNATURE = b"\x1a\x45\xdf\xa3"
_HTML_MARKERS = ("<!doctype", "<html", "<script", "<iframe", "<svg")


def _upload_head(value, length=8192):
    """Read a bounded prefix for sniffing and restore the upload pointer."""
    try:
        value.seek(0)
        head = value.read(length)
        value.seek(0)
    except (AttributeError, OSError, ValueError):
        return b""
    return head or b""


def _is_plain_text(head):
    try:
        text = head.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    if "\x00" in text:
        return False
    if any(ord(char) < 32 and char not in "\t\n\r\f" for char in text):
        return False
    lowered = text[:4096].lstrip().lower()
    return not any(marker in lowered for marker in _HTML_MARKERS)


def _matches_upload_content(extension, head):
    """Return True when the sniffed bytes match the allowlisted extension."""
    if not head:
        return False
    if extension == ".pdf":
        return head.startswith(_PDF_SIGNATURE)
    if extension == ".png":
        return head.startswith(_PNG_SIGNATURE)
    if extension in {".jpg", ".jpeg"}:
        return head.startswith(_JPEG_SIGNATURE)
    if extension == ".gif":
        return head.startswith(_GIF_SIGNATURES)
    if extension == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if extension in {".doc", ".ppt", ".xls"}:
        return head.startswith(_OLE2_SIGNATURE)
    if extension in {".docx", ".pptx", ".xlsx"}:
        return head.startswith(_ZIP_SIGNATURES)
    if extension in {".txt", ".csv"}:
        return _is_plain_text(head)
    if extension == ".mp3":
        return head.startswith(_MP3_SIGNATURES)
    if extension == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if extension == ".ogg":
        return head.startswith(b"OggS")
    if extension == ".mp4":
        return head[4:8] == b"ftyp"
    if extension == ".webm":
        return head.startswith(_EBML_SIGNATURE)
    return False


def _safe_image_url(value):
    """Return a browser URL without exposing a storage path."""
    name = getattr(value, "name", "")
    if not name:
        return ""
    # Curated catalogue artwork is served by the frontend's public /images/
    # folder. Uploaded artwork uses Django's public MEDIA_URL.
    if name.startswith("/images/"):
        return name
    try:
        return value.url
    except (ValueError, OSError):
        return ""


def _validate_image_upload(value):
    """Accept only real JPG, PNG or WebP artwork within the upload limit."""
    extension = os.path.splitext(value.name)[1].lower()
    allowed = {
        ".jpg": "JPEG", ".jpeg": "JPEG",
        ".png": "PNG", ".webp": "WEBP",
    }
    if extension not in allowed:
        raise serializers.ValidationError("Use a JPG, PNG or WebP image.")
    if value.size > _max_upload_bytes():
        limit_mb = round(_max_upload_bytes() / (1024 * 1024))
        raise serializers.ValidationError(f"Images must be {limit_mb} MB or smaller.")
    content_type = getattr(value, "content_type", "") or ""
    if content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise serializers.ValidationError("The image media type is not allowed.")
    try:
        value.seek(0)
        with Image.open(value) as image:
            image_format = image.format
            image.verify()
    except (
        Image.DecompressionBombError, UnidentifiedImageError, OSError,
        SyntaxError, ValueError,
    ):
        raise serializers.ValidationError("The file is not a readable image.") from None
    finally:
        try:
            value.seek(0)
        except (AttributeError, OSError, ValueError):
            pass
    if image_format != allowed[extension]:
        raise serializers.ValidationError("The image contents do not match its file name.")
    return value


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "code", "website", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ResourceCollectionSerializer(serializers.ModelSerializer):
    resource_count = serializers.IntegerField(source="resources.count", read_only=True)

    class Meta:
        model = ResourceCollection
        fields = ["id", "name", "slug", "description", "resource_count", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class EmbedProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbedProvider
        fields = ["id", "name", "host", "kind", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", EmbedProviderKind.YOUTUBE))
        raw_host = attrs.get("host", getattr(self.instance, "host", ""))
        host = normalise_host(raw_host)
        allowed = {normalise_host(item) for item in HOSTS_BY_KIND.get(kind, set())}
        if host not in allowed:
            raise serializers.ValidationError(
                {"host": "Choose a known host for this provider, such as www.youtube.com."}
            )
        attrs["host"] = host
        return attrs


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = [
            "id", "textbook", "title", "chapter_number", "content",
            "learning_outcome", "is_downloadable", "sequence", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ContentResourceSerializer(serializers.ModelSerializer):
    """Curator-facing resource form. Never use this for public/portal reads."""

    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    embed_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    level_name = serializers.CharField(source="education_level.name", read_only=True)
    area_name = serializers.CharField(source="learning_area.name", read_only=True)

    class Meta:
        model = ContentResource
        fields = [
            "id", "title", "description", "resource_type", "delivery", "file", "file_url",
            "thumbnail_image", "thumbnail_url", "external_url", "embed_provider", "embed_source_url", "embed_url", "download_url",
            "chapter", "textbook", "institution", "education_level", "learning_area",
            "subject", "school_class", "collection", "level_name", "area_name",
            "keywords", "offline_available", "size_kb", "status", "published_at",
            "access_scope", "created_at", "updated_at",
        ]
        read_only_fields = [
            "file_url", "thumbnail_url", "embed_url", "download_url", "level_name",
            "area_name", "created_at", "updated_at",
        ]

    def get_file_url(self, obj):
        return obj.file.url if obj.file else ""

    def get_thumbnail_url(self, obj):
        return _safe_image_url(obj.thumbnail_image)

    def get_embed_url(self, obj):
        return obj.build_embed_url()

    def get_download_url(self, obj):
        return reverse("contentresource-download", args=[obj.pk]) if obj.file else ""

    def validate_file(self, value):
        extension = os.path.splitext(value.name)[1].lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                "This file type is not allowed. Use a document, image, audio or video file."
            )
        if value.size > _max_upload_bytes():
            limit_mb = round(_max_upload_bytes() / (1024 * 1024))
            raise serializers.ValidationError(f"Files must be {limit_mb} MB or smaller.")
        content_type = getattr(value, "content_type", "") or ""
        if content_type and content_type not in ALLOWED_UPLOAD_MIME:
            raise serializers.ValidationError("The file's media type is not allowed.")
        if not _matches_upload_content(extension, _upload_head(value)):
            raise serializers.ValidationError(
                "The file contents do not match its file type."
            )
        return value

    def validate_thumbnail_image(self, value):
        return _validate_image_upload(value) if value else value

    def validate_external_url(self, value):
        if value and not _is_https(value):
            raise serializers.ValidationError("External links must use HTTPS.")
        return value

    def validate_embed_source_url(self, value):
        if any(char in str(value or "") for char in "<>\"'"):
            raise serializers.ValidationError("Enter a plain video URL, not HTML or markup.")
        return value

    def validate_keywords(self, value):
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise serializers.ValidationError("Keywords must be a list of text values.")
        return [item.strip()[:60] for item in value if item.strip()]

    def validate(self, attrs):
        instance = self.instance
        delivery = attrs.get("delivery", getattr(instance, "delivery", ResourceDelivery.UPLOAD))
        scope = attrs.get("access_scope", getattr(instance, "access_scope", ResourceAccessScope.PUBLIC))
        status = attrs.get("status", getattr(instance, "status", ContentStatus.DRAFT))

        # Exactly one source of content is kept, so a stale link cannot leak
        # into a newly uploaded resource.
        if delivery == ResourceDelivery.UPLOAD:
            attrs["external_url"] = ""
            attrs["embed_provider"] = None
            attrs["embed_source_url"] = ""
        elif delivery == ResourceDelivery.LINK:
            attrs["file"] = None
            attrs["embed_provider"] = None
            attrs["embed_source_url"] = ""
        elif delivery == ResourceDelivery.EMBED:
            attrs["file"] = None
            attrs["external_url"] = ""

        if delivery == ResourceDelivery.UPLOAD:
            uploaded = attrs.get("file")
            if uploaded:
                attrs["size_kb"] = max(1, round(uploaded.size / 1024))
            elif not (instance and instance.file):
                raise serializers.ValidationError({"file": "Choose a file for a local upload."})
        elif delivery == ResourceDelivery.LINK:
            if not attrs.get("external_url"):
                raise serializers.ValidationError({"external_url": "Enter the HTTPS link."})
        elif delivery == ResourceDelivery.EMBED:
            provider = attrs.get("embed_provider") or (instance.embed_provider if instance else None)
            source = attrs.get("embed_source_url") or (instance.embed_source_url if instance else "")
            if not provider or not provider.is_active:
                raise serializers.ValidationError({"embed_provider": "Choose an active, approved provider."})
            if not ContentResource(
                delivery=ResourceDelivery.EMBED, embed_provider=provider, embed_source_url=source,
            ).build_embed_url():
                raise serializers.ValidationError(
                    {"embed_source_url": "Enter a valid HTTPS video URL for that provider."}
                )

        institution = attrs.get("institution") or (instance.institution if instance else None)
        if scope != ResourceAccessScope.PUBLIC and not institution:
            raise serializers.ValidationError(
                {"institution": "School or class resources need an institution."}
            )
        if scope == ResourceAccessScope.CLASS:
            school_class = attrs.get("school_class") or (instance.school_class if instance else None)
            if not school_class:
                raise serializers.ValidationError({"school_class": "Class-scoped resources need a class."})
            if institution and school_class.institution_id != getattr(institution, "pk", institution):
                raise serializers.ValidationError(
                    {"school_class": "Choose a class from the selected institution."}
                )

        if status == ContentStatus.PUBLISHED and not attrs.get("published_at"):
            attrs["published_at"] = timezone.now()
        return attrs


class _SafeResourceFieldsMixin(serializers.Serializer):
    """Fields shared by anonymous and portal resource readers.

    This inherits from Serializer so DRF's metaclass registers the declared
    fields for both concrete resource serializers.
    """

    level_name = serializers.CharField(source="education_level.name", read_only=True)
    area_name = serializers.CharField(source="learning_area.name", read_only=True)
    collection_name = serializers.CharField(source="collection.name", read_only=True)
    embed_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    file_available = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    SAFE_FIELDS = [
        "id", "title", "description", "resource_type", "delivery", "external_url",
        "embed_url", "download_url", "file_available", "thumbnail_url", "education_level",
        "level_name", "learning_area", "area_name", "collection", "collection_name",
        "keywords", "offline_available", "size_kb", "published_at",
    ]

    def get_embed_url(self, obj):
        return obj.build_embed_url() if obj.delivery == ResourceDelivery.EMBED else ""

    def get_external_url(self, obj):
        if obj.delivery == ResourceDelivery.LINK and _is_https(obj.external_url):
            return obj.external_url
        return ""

    def get_download_url(self, obj):
        return reverse("contentresource-download", args=[obj.pk]) if obj.file else ""

    def get_file_available(self, obj):
        return bool(obj.file)

    def get_thumbnail_url(self, obj):
        return _safe_image_url(obj.thumbnail_image)


class ContentResourcePublicSerializer(_SafeResourceFieldsMixin, serializers.ModelSerializer):
    """Anonymous-safe catalogue representation: no storage paths or drafts."""

    external_url = serializers.SerializerMethodField()

    class Meta:
        model = ContentResource
        fields = _SafeResourceFieldsMixin.SAFE_FIELDS
        read_only_fields = fields


class ContentResourcePortalSerializer(_SafeResourceFieldsMixin, serializers.ModelSerializer):
    """Authenticated portal representation, including school taxonomy."""

    external_url = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    class_name = serializers.CharField(source="school_class.name", read_only=True)

    class Meta:
        model = ContentResource
        fields = _SafeResourceFieldsMixin.SAFE_FIELDS + [
            "subject", "subject_name", "school_class", "class_name", "access_scope",
        ]
        read_only_fields = fields


class ExerciseSerializer(serializers.ModelSerializer):
    attempt_count = serializers.IntegerField(source="attempts.count", read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id", "chapter", "title", "instructions", "questions", "max_score",
            "sequence", "attempt_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DigitalTextbookSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    chapter_count = serializers.IntegerField(source="chapters.count", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = DigitalTextbook
        fields = [
            "id", "publisher", "publisher_name", "title", "subtitle", "isbn",
            "subject", "subject_name", "education_level", "curriculum_framework",
            "description", "cover_image", "license_type", "status", "published_at",
            "chapter_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PublicTextbookSerializer(serializers.ModelSerializer):
    """Anonymous catalogue preview. Full book access stays licence controlled."""

    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    level_name = serializers.CharField(source="education_level.name", read_only=True)
    chapter_count = serializers.IntegerField(source="chapters.count", read_only=True)
    access_label = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = DigitalTextbook
        fields = [
            "id", "title", "subtitle", "publisher_name", "subject_name",
            "level_name", "description", "chapter_count", "access_label", "cover_url",
        ]
        read_only_fields = fields

    def get_cover_url(self, obj):
        return _safe_image_url(obj.cover_image)

    def get_access_label(self, obj):
        return "Open access" if obj.license_type == "OPEN" else "School access"


class TextbookDetailSerializer(DigitalTextbookSerializer):
    chapters = serializers.SerializerMethodField()

    def get_chapters(self, obj):
        chapters = obj.chapters.prefetch_related("exercises", "resources")
        return ChapterDetailSerializer(chapters, many=True, context=self.context).data


class ChapterDetailSerializer(ChapterSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    resources = ContentResourcePortalSerializer(many=True, read_only=True)


def _is_staff_user(user):
    return is_staff_user(user)


def _check_related_institution(user, obj, label):
    if not same_institution(user, obj.institution_id):
        raise serializers.ValidationError(f"The {label} belongs to another institution.")


def _check_own_learner(user, learner):
    if _is_staff_user(user):
        return
    own = getattr(user, "learner_profile", None)
    if own is None or own.pk != learner.pk:
        raise serializers.ValidationError("You may only record work for yourself.")


class CurrentLearnerDefault:
    """Fill the learner from the request so non-staff cannot choose another."""

    requires_context = True

    def __call__(self, serializer_field):
        request = serializer_field.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or _is_staff_user(user):
            return None
        return getattr(user, "learner_profile", None)


class ExerciseAttemptSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    exercise_title = serializers.CharField(source="exercise.title", read_only=True)

    class Meta:
        model = ExerciseAttempt
        fields = [
            "id", "institution", "exercise", "learner", "learner_name", "exercise_title",
            "answers", "score", "completed_at", "synced_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "institution", "score", "completed_at", "synced_at", "created_at", "updated_at",
        ]
        extra_kwargs = {
            "learner": {
                "required": False,
                "allow_null": True,
                "default": CurrentLearnerDefault(),
            },
        }

    def to_internal_value(self, data):
        # Non-staff ownership is never chosen by the client. Drop the fields
        # before validation so the server-derived learner is the only value.
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not _is_staff_user(user):
            data = data.copy()
            data.pop("learner", None)
            data.pop("institution", None)
        return super().to_internal_value(data)

    def validate_learner(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request:
            _check_related_institution(request.user, value, "learner")
            _check_own_learner(request.user, value)
        return value


class ContentAccessSerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source="textbook.title", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)

    class Meta:
        model = ContentAccess
        fields = [
            "id", "institution", "institution_name", "textbook",
            "textbook_title", "licence_reference", "valid_from", "valid_until",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
