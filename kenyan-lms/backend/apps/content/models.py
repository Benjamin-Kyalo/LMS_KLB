"""Digital textbooks, chapters and linked learning resources."""
import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.core.constants import (
    ContentStatus, EmbedProviderKind, ResourceAccessScope, ResourceDelivery,
)
from apps.core.models import AutoReferenceModelMixin, InstitutionScopedModel, TimeStampedModel

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
VIMEO_HOSTS = {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIMEO_ID_RE = re.compile(r"^\d+$")
HOST_RE = re.compile(r"^[a-z0-9.-]+$")
HOSTS_BY_KIND = {
    EmbedProviderKind.YOUTUBE: YOUTUBE_HOSTS,
    EmbedProviderKind.VIMEO: VIMEO_HOSTS,
}


class Publisher(AutoReferenceModelMixin, TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DigitalTextbook(AutoReferenceModelMixin, TimeStampedModel):
    """A title in the catalogue. Access is controlled separately per institution."""

    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="textbooks")
    title = models.CharField(max_length=250)
    subtitle = models.CharField(max_length=250, blank=True)
    isbn = models.CharField(max_length=30, blank=True, db_index=True)
    subject = models.ForeignKey("institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    education_level = models.ForeignKey("curriculum.EducationLevel", on_delete=models.SET_NULL, null=True, blank=True)
    curriculum_framework = models.ForeignKey("curriculum.CurriculumFramework", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="content/covers/", null=True, blank=True)
    license_type = models.CharField(
        max_length=30, default="INSTITUTION",
        choices=[("OPEN", "Open"), ("INSTITUTION", "Institution licence"), ("PER_LEARNER", "Per learner"), ("EXPIRED", "Expired")],
    )
    status = models.CharField(max_length=20, choices=ContentStatus.CHOICES, default=ContentStatus.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["status", "subject", "education_level"])]

    def __str__(self):
        return self.title


class Chapter(AutoReferenceModelMixin, TimeStampedModel):
    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    chapter_number = models.PositiveSmallIntegerField(default=1)
    content = models.TextField(blank=True)
    learning_outcome = models.ForeignKey("curriculum.LearningOutcome", on_delete=models.SET_NULL, null=True, blank=True)
    is_downloadable = models.BooleanField(default=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["textbook", "sequence", "chapter_number"]
        constraints = [
            models.UniqueConstraint(fields=["textbook", "chapter_number"], name="unique_chapter_number")
        ]

    def __str__(self):
        return f"{self.textbook.title} - {self.title}"


class ResourceCollection(TimeStampedModel):
    """An admin-managed grouping used to make the catalogue easier to browse."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "collection"
            candidate = base
            suffix = 2
            while ResourceCollection.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        return super().save(*args, **kwargs)


class EmbedProvider(TimeStampedModel):
    """A curated allowlist entry. No arbitrary iframe or script HTML is stored."""

    name = models.CharField(max_length=100, unique=True)
    host = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=20, choices=EmbedProviderKind.CHOICES, default=EmbedProviderKind.YOUTUBE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        host = normalise_host(self.host)
        allowed = {normalise_host(item) for item in HOSTS_BY_KIND.get(self.kind, set())}
        if not host or not HOST_RE.fullmatch(host) or host not in allowed:
            raise ValidationError(
                {"host": "Choose a known host for this provider, such as www.youtube.com."}
            )
        self.host = host

    def save(self, *args, **kwargs):
        self.host = normalise_host(self.host)
        return super().save(*args, **kwargs)


def normalise_host(value):
    """Reduce an admin-entered host to a comparable lowercase hostname."""
    host = str(value or "").strip().lower()
    if "://" in host:
        host = urlparse(host).netloc
    return host.strip("/").split("/")[0]


def extract_video_id(provider, source_url):
    """Return a validated provider video ID, or an empty string."""
    try:
        parsed = urlparse(str(source_url or ""))
    except ValueError:
        return ""
    host = normalise_host(parsed.netloc)
    if parsed.scheme != "https" or not host:
        return ""
    # The admin-managed allowlist entry must match the source URL host. An
    # inactive or mismatched provider cannot silently authorise another site.
    if not provider.is_active or host != normalise_host(provider.host):
        return ""

    if provider.kind == EmbedProviderKind.YOUTUBE:
        if host not in {normalise_host(item) for item in YOUTUBE_HOSTS}:
            return ""
        parts = [part for part in parsed.path.split("/") if part]
        if host == "youtu.be":
            candidate = parts[0] if parts else ""
        elif parts and parts[0] in {"embed", "shorts", "live"}:
            candidate = parts[1] if len(parts) > 1 else ""
        else:
            candidate = (parse_qs(parsed.query).get("v") or [""])[0]
        return candidate if YOUTUBE_ID_RE.fullmatch(candidate) else ""

    if provider.kind == EmbedProviderKind.VIMEO:
        if host not in {normalise_host(item) for item in VIMEO_HOSTS}:
            return ""
        parts = [part for part in parsed.path.split("/") if part]
        candidate = parts[0] if parts else ""
        return candidate if VIMEO_ID_RE.fullmatch(candidate) else ""
    return ""


class ContentResource(TimeStampedModel):
    """A file, validated link or curated embed linked to a chapter or standalone."""

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True, related_name="resources")
    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, null=True, blank=True, related_name="resources")
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="content_resources",
    )
    education_level = models.ForeignKey(
        "curriculum.EducationLevel", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resources",
    )
    learning_area = models.ForeignKey(
        "curriculum.LearningArea", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resources",
    )
    subject = models.ForeignKey(
        "institutions.Subject", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="content_resources",
    )
    school_class = models.ForeignKey(
        "institutions.SchoolClass", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="content_resources",
    )
    collection = models.ForeignKey(
        ResourceCollection, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resources",
    )
    title = models.CharField(max_length=200)
    resource_type = models.CharField(
        max_length=20, default="PDF",
        choices=[("PDF", "PDF"), ("VIDEO", "Video"), ("AUDIO", "Audio"), ("IMAGE", "Image"), ("INTERACTIVE", "Interactive"), ("LINK", "External link")],
    )
    delivery = models.CharField(
        max_length=10, choices=ResourceDelivery.CHOICES, default=ResourceDelivery.UPLOAD, db_index=True,
    )
    file = models.FileField(upload_to="content/resources/", null=True, blank=True)
    thumbnail_image = models.ImageField(upload_to="content/resource-thumbnails/", null=True, blank=True)
    external_url = models.URLField(blank=True)
    embed_provider = models.ForeignKey(
        EmbedProvider, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resources",
    )
    embed_source_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    offline_available = models.BooleanField(default=False)
    size_kb = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=ContentStatus.CHOICES, default=ContentStatus.DRAFT, db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    access_scope = models.CharField(
        max_length=20, choices=ResourceAccessScope.CHOICES,
        default=ResourceAccessScope.PUBLIC, db_index=True,
    )

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["status", "access_scope", "published_at"]),
            models.Index(fields=["education_level", "learning_area"]),
            models.Index(fields=["institution", "school_class", "subject"]),
        ]

    def __str__(self):
        return self.title

    def build_embed_url(self):
        """Build the only iframe URL the frontend is allowed to render."""
        if self.delivery != ResourceDelivery.EMBED or not self.embed_provider_id:
            return ""
        video_id = extract_video_id(self.embed_provider, self.embed_source_url)
        if not video_id:
            return ""
        if self.embed_provider.kind == EmbedProviderKind.YOUTUBE:
            return f"https://www.youtube.com/embed/{video_id}"
        if self.embed_provider.kind == EmbedProviderKind.VIMEO:
            return f"https://player.vimeo.com/video/{video_id}"
        return ""

    def clean(self):
        errors = {}
        if self.access_scope != ResourceAccessScope.PUBLIC and not self.institution_id:
            errors["institution"] = "Choose the institution this resource belongs to."
        if self.access_scope == ResourceAccessScope.CLASS and not self.school_class_id:
            errors["school_class"] = "Class-scoped resources need a class."
        if self.delivery == ResourceDelivery.UPLOAD and not self.file:
            errors["file"] = "Upload a file, or choose a different delivery method."
        if self.delivery == ResourceDelivery.LINK:
            if not str(self.external_url).startswith("https://"):
                errors["external_url"] = "External links must use HTTPS."
        if self.delivery == ResourceDelivery.EMBED:
            if not self.embed_provider_id or not self.embed_provider.is_active:
                errors["embed_provider"] = "Choose an active, administrator-approved provider."
            elif not self.build_embed_url():
                errors["embed_source_url"] = "Enter a valid HTTPS video URL for the selected provider."
        if errors:
            raise ValidationError(errors)


class Exercise(TimeStampedModel):
    """An exercise attached to a chapter. Questions are stored as JSON for flexibility."""

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="exercises")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    questions = models.JSONField(default=list)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["chapter", "sequence"]


class ExerciseAttempt(InstitutionScopedModel):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    learner = models.ForeignKey("learners.Learner", on_delete=models.CASCADE, related_name="exercise_attempts")
    answers = models.JSONField(default=list)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [models.Index(fields=["institution", "learner", "exercise"])]


class ContentAccess(AutoReferenceModelMixin, InstitutionScopedModel):
    """Grants an institution access to a textbook under a licence."""

    textbook = models.ForeignKey(DigitalTextbook, on_delete=models.CASCADE, related_name="access_grants")
    licence_reference = models.CharField(max_length=100, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["institution", "textbook"], name="unique_textbook_access")
        ]
