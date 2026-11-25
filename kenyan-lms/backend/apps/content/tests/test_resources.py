"""Phase 2 resource catalogue, taxonomy and scoped download tests."""
import base64
import shutil
import tempfile
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.content.models import (
    ContentResource, DigitalTextbook, EmbedProvider, Publisher, ResourceCollection,
)
from apps.core.constants import (
    ContentStatus, EmbedProviderKind, ResourceAccessScope, ResourceDelivery, Roles,
)
from apps.curriculum.models import CurriculumFramework, EducationLevel, LearningArea
from apps.guardians.models import Guardian
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass, Subject
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


class ResourceCatalogueTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Resource Type", code="RST")
        self.school = Institution.objects.create(
            name="Resource School", code="RSH", institution_type=kind,
        )
        self.other_school = Institution.objects.create(
            name="Other Resource School", code="ORS", institution_type=kind,
        )
        year = AcademicYear.objects.create(
            institution=self.school, name="2026", start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.school_class = SchoolClass.objects.create(
            institution=self.school, academic_year=year, name="Grade 5",
        )
        self.subject = Subject.objects.create(institution=self.school, name="Mathematics")
        framework = CurriculumFramework.objects.create(name="Test CBC", code="TCBC")
        level = EducationLevel.objects.create(framework=framework, name="Grade 5", code="G5")
        self.area = LearningArea.objects.create(level=level, name="Mathematics")
        self.collection = ResourceCollection.objects.create(name="Revision collection")
        self.publisher = Publisher.objects.create(name="Catalogue Publisher", code="CAT")
        self.provider = EmbedProvider.objects.create(
            name="Test YouTube", host="www.youtube.com", kind=EmbedProviderKind.YOUTUBE,
        )

        self.admin = User.objects.create_user(
            username="resource_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school,
        )
        self.learner = User.objects.create_user(
            username="resource_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner_profile = Learner.objects.create(
            user=self.learner, institution=self.school, admission_number="RSH-001",
            class_room=self.school_class,
        )
        guardian_user = User.objects.create_user(
            username="resource_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=self.school,
        )
        self.guardian = Guardian.objects.create(user=guardian_user, institution=self.school)
        self.guardian_user = guardian_user
        self.other_learner = User.objects.create_user(
            username="other_resource_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.other_school,
        )

        self.public = self.make_resource("Public fractions", ResourceAccessScope.PUBLIC)
        self.draft = self.make_resource(
            "Draft fractions", ResourceAccessScope.PUBLIC, status_value=ContentStatus.DRAFT,
        )
        self.school_only = self.make_resource(
            "School fractions", ResourceAccessScope.INSTITUTION, institution=self.school,
        )
        self.other_school_only = self.make_resource(
            "Other school fractions", ResourceAccessScope.INSTITUTION,
            institution=self.other_school,
        )
        self.class_only = self.make_resource(
            "Class fractions", ResourceAccessScope.CLASS,
            institution=self.school, school_class=self.school_class,
        )

    def make_book(self, title, *, license_type="INSTITUTION",
                  status_value=ContentStatus.PUBLISHED):
        return DigitalTextbook.objects.create(
            publisher=self.publisher,
            title=title,
            description="A sample catalogue title.",
            subject=self.subject,
            education_level=self.area.level,
            isbn=f"978-000-{DigitalTextbook.objects.count() + 1:05d}",
            license_type=license_type,
            status=status_value,
            published_at=timezone.now() if status_value == ContentStatus.PUBLISHED else None,
        )

    def make_resource(self, title, scope, *, institution=None, school_class=None,
                      status_value=ContentStatus.PUBLISHED):
        return ContentResource.objects.create(
            title=title,
            description="A sample resource for catalogue tests.",
            resource_type="PDF",
            delivery=ResourceDelivery.LINK,
            external_url="https://example.test/resource",
            education_level=self.area.level,
            learning_area=self.area,
            collection=self.collection,
            keywords=["fractions", "revision"],
            status=status_value,
            published_at=timezone.now() if status_value == ContentStatus.PUBLISHED else None,
            access_scope=scope,
            institution=institution,
            school_class=school_class,
        )

    def test_public_catalogue_is_anonymous_and_hides_private_or_draft_resources(self):
        response = self.client.get(reverse("public-resource-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.public.id, ids)
        self.assertNotIn(self.draft.id, ids)
        self.assertNotIn(self.school_only.id, ids)
        self.assertNotIn(self.other_school_only.id, ids)
        self.assertNotIn(self.class_only.id, ids)

        row = next(row for row in response.data["results"] if row["id"] == self.public.id)
        for forbidden in ("file", "institution", "school_class", "created_at", "updated_at"):
            self.assertNotIn(forbidden, row)
        self.assertEqual(row["collection_name"], self.collection.name)
        self.assertEqual(row["level_name"], self.area.level.name)

    def test_public_book_catalogue_hides_drafts_and_expired_titles(self):
        open_book = self.make_book("Open fractions", license_type="OPEN")
        school_book = self.make_book("School fractions")
        draft = self.make_book("Draft fractions", status_value=ContentStatus.DRAFT)
        expired = self.make_book("Expired fractions", license_type="EXPIRED")

        response = self.client.get(reverse("public-book-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(open_book.id, ids)
        self.assertIn(school_book.id, ids)
        self.assertNotIn(draft.id, ids)
        self.assertNotIn(expired.id, ids)

        row = next(row for row in response.data["results"] if row["id"] == open_book.id)
        self.assertEqual(row["access_label"], "Open access")
        self.assertEqual(row["publisher_name"], self.publisher.name)
        for forbidden in ("publisher", "status", "published_at", "license_type", "isbn", "created_at"):
            self.assertNotIn(forbidden, row)

    def test_catalogue_search_accepts_the_q_parameter(self):
        self.make_book("Fractions made simple")
        self.make_book("Earth science")
        response = self.client.get(reverse("public-book-list"), {"q": "Fractions"})
        self.assertEqual([row["title"] for row in response.data["results"]], ["Fractions made simple"])

        public_resource = self.client.get(reverse("public-resource-list"), {"q": "Public"})
        self.assertIn(self.public.id, [row["id"] for row in public_resource.data["results"]])

    def test_public_facets_are_anonymous_and_school_taxonomy_is_authenticated(self):
        response = self.client.get(reverse("resource-facets"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["levels"][0]["id"], self.area.level_id)
        self.assertEqual(response.data["levels"][0]["learning_areas"][0]["id"], self.area.id)
        self.assertNotIn("subjects", response.data)
        self.assertNotIn("classes", response.data)

        self.client.force_authenticate(user=self.learner)
        response = self.client.get(reverse("resource-facets"))
        self.assertEqual([row["id"] for row in response.data["subjects"]], [self.subject.id])
        self.assertEqual([row["id"] for row in response.data["classes"]], [self.school_class.id])

    def test_portal_catalogue_scopes_public_institution_and_class_resources(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(reverse("portal-resource-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.public.id, ids)
        self.assertIn(self.school_only.id, ids)
        self.assertIn(self.class_only.id, ids)
        self.assertNotIn(self.other_school_only.id, ids)
        self.assertNotIn(self.draft.id, ids)

        self.client.force_authenticate(user=self.other_learner)
        response = self.client.get(reverse("portal-resource-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.other_school_only.id, ids)
        self.assertNotIn(self.school_only.id, ids)
        self.assertNotIn(self.class_only.id, ids)

    def test_unverified_guardian_cannot_open_class_scoped_resources(self):
        link = LearnerGuardian.objects.create(
            learner=self.learner_profile, guardian=self.guardian, is_verified=False,
        )
        self.client.force_authenticate(user=self.guardian_user)
        response = self.client.get(reverse("portal-resource-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.class_only.id, ids)
        self.assertIn(self.school_only.id, ids)

        link.is_verified = True
        link.save(update_fields=["is_verified"])
        response = self.client.get(reverse("portal-resource-list"))
        self.assertIn(self.class_only.id, [row["id"] for row in response.data["results"]])

    def test_portal_documents_only_return_document_types(self):
        video = self.make_resource("Mathematics video", ResourceAccessScope.PUBLIC)
        video.resource_type = "VIDEO"
        video.save(update_fields=["resource_type"])
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(reverse("portal-document-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(video.id, [row["id"] for row in response.data["results"]])
        self.assertIn(self.public.id, [row["id"] for row in response.data["results"]])

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-resource-tests-"))
    def test_admin_uploads_a_file_and_download_respects_scope(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        upload = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 sample", content_type="application/pdf")
        response = self.client.post(reverse("contentresource-list"), {
            "title": "School notes",
            "resource_type": "PDF",
            "delivery": ResourceDelivery.UPLOAD,
            "file": upload,
            "status": ContentStatus.PUBLISHED,
            "access_scope": ResourceAccessScope.INSTITUTION,
            "institution": self.school.id,
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        download_url = reverse("contentresource-download", args=[response.data["id"]])

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(download_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.other_learner)
        self.assertEqual(self.client.get(download_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", response["Content-Disposition"])

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-public-file-tests-"))
    def test_anonymous_user_can_download_a_public_file(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        resource = ContentResource.objects.create(
            title="Public file", delivery=ResourceDelivery.UPLOAD,
            status=ContentStatus.PUBLISHED, published_at=timezone.now(),
            access_scope=ResourceAccessScope.PUBLIC,
        )
        resource.file.save("public-notes.pdf", SimpleUploadedFile(
            "public-notes.pdf", b"%PDF-1.4 public sample", content_type="application/pdf",
        ), save=True)

        response = self.client.get(reverse("contentresource-download", args=[resource.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_embed_validation_only_accepts_allowlisted_https_video_urls(self):
        self.client.force_authenticate(user=self.admin)
        valid = self.client.post(reverse("contentresource-list"), {
            "title": "Counting video",
            "resource_type": "VIDEO",
            "delivery": ResourceDelivery.EMBED,
            "embed_provider": self.provider.id,
            "embed_source_url": "https://www.youtube.com/watch?v=abcdefghijk",
            "status": ContentStatus.PUBLISHED,
            "access_scope": ResourceAccessScope.PUBLIC,
        }, format="json")
        self.assertEqual(valid.status_code, status.HTTP_201_CREATED, valid.data)
        self.assertEqual(
            valid.data["embed_url"], "https://www.youtube.com/embed/abcdefghijk",
        )
        self.assertNotIn("<iframe", valid.data["embed_url"])

        for invalid in (
            "<iframe src='https://www.youtube.com/embed/abcdefghijk'></iframe>",
            "https://evil.test/watch?v=abcdefghijk",
            "http://www.youtube.com/watch?v=abcdefghijk",
        ):
            with self.subTest(invalid=invalid):
                response = self.client.post(reverse("contentresource-list"), {
                    "title": "Invalid embed",
                    "resource_type": "VIDEO",
                    "delivery": ResourceDelivery.EMBED,
                    "embed_provider": self.provider.id,
                    "embed_source_url": invalid,
                }, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-invalid-upload-tests-"))
    def test_disallowed_upload_extensions_are_rejected(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        upload = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(reverse("contentresource-list"), {
            "title": "Invalid upload",
            "delivery": ResourceDelivery.UPLOAD,
            "resource_type": "PDF",
            "file": upload,
        }, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def post_upload(self, filename, payload, content_type, **extra):
        data = {
            "title": extra.pop("title", "Uploaded resource"),
            "resource_type": extra.pop("resource_type", "PDF"),
            "delivery": ResourceDelivery.UPLOAD,
            "file": SimpleUploadedFile(filename, payload, content_type=content_type),
        }
        data.update(extra)
        return self.client.post(reverse("contentresource-list"), data, format="multipart")

    def test_ordinary_users_get_a_scoped_and_safe_resource_list(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(reverse("contentresource-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        rows = response.data["results"]
        ids = [row["id"] for row in rows]
        self.assertIn(self.public.id, ids)
        self.assertIn(self.school_only.id, ids)
        self.assertIn(self.class_only.id, ids)
        self.assertNotIn(self.draft.id, ids)
        self.assertNotIn(self.other_school_only.id, ids)
        for row in rows:
            for forbidden in (
                "file", "file_url", "status", "institution", "created_at",
                "updated_at", "embed_source_url", "embed_provider",
            ):
                self.assertNotIn(forbidden, row)
            self.assertIn("file_available", row)
            self.assertIn("download_url", row)

    def test_ordinary_user_cannot_retrieve_foreign_or_draft_resources(self):
        self.client.force_authenticate(user=self.learner)
        for resource in (self.draft, self.other_school_only):
            with self.subTest(resource=resource.title):
                response = self.client.get(
                    reverse("contentresource-detail", args=[resource.id])
                )
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(reverse("contentresource-detail", args=[self.school_only.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["title"], self.school_only.title)
        for forbidden in ("file", "file_url", "status", "institution"):
            self.assertNotIn(forbidden, response.data)

    def test_managers_keep_the_full_administrative_resource_view(self):
        curator = User.objects.create_user(
            username="resource_curator", password="StrongPass123!",
            role=Roles.ADMIN,
        )
        for user in (self.admin, curator):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)
                response = self.client.get(reverse("contentresource-list"))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
                row = next(row for row in response.data["results"] if row["id"] == self.draft.id)
                for expected in ("file", "file_url", "status", "institution"):
                    self.assertIn(expected, row)
                detail = self.client.get(
                    reverse("contentresource-detail", args=[self.other_school_only.id])
                )
                self.assertEqual(detail.status_code, status.HTTP_200_OK)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-magic-byte-tests-"))
    def test_upload_rejects_pdf_named_files_with_html_or_elf_bytes(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        for payload in (
            b"<!DOCTYPE html><html><body>not a pdf</body></html>",
            b"\x7fELF\x02\x01\x01\x00binary payload",
        ):
            with self.subTest(prefix=payload[:8]):
                response = self.post_upload("notes.pdf", payload, "application/pdf")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("file", response.data)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-valid-magic-tests-"))
    def test_upload_accepts_valid_small_pdf_and_png(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8Dw"
            "HwAFAAH/q842iQAAAABJRU5ErkJggg=="
        )
        for filename, payload, media_type in (
            ("notes.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf"),
            ("picture.png", png, "image/png"),
        ):
            with self.subTest(filename=filename):
                response = self.post_upload(filename, payload, media_type)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
                self.assertTrue(response.data["file_url"])

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-content-type-tests-"))
    def test_client_content_type_cannot_authorise_mismatched_bytes(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        html = b"<html><body>not a binary file</body></html>"
        for filename, media_type in (
            ("notes.pdf", "text/plain"),
            ("picture.png", "image/png"),
        ):
            with self.subTest(filename=filename):
                response = self.post_upload(filename, html, media_type)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("file", response.data)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-document-sniff-tests-"))
    def test_text_and_office_uploads_check_their_contents(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        docx_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        invalid = (
            ("notes.txt", b"Binary\x00text", "text/plain"),
            ("notes.csv", b"<!DOCTYPE html><html></html>", "text/csv"),
            ("slides.docx", b"<html></html>", docx_type),
        )
        for filename, payload, media_type in invalid:
            with self.subTest(filename=filename, payload=payload[:8]):
                response = self.post_upload(filename, payload, media_type)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("file", response.data)

        for filename, payload, media_type in (
            ("notes.txt", b"Hello class\n", "text/plain"),
            ("slides.docx", b"PK\x03\x04minimal docx", docx_type),
        ):
            with self.subTest(filename=filename):
                response = self.post_upload(filename, payload, media_type)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    @override_settings(
        MEDIA_ROOT=tempfile.mkdtemp(prefix="lms-size-tests-"),
        CONTENT_RESOURCE_MAX_UPLOAD_BYTES=8,
    )
    def test_oversized_upload_is_still_rejected(self):
        media_root = settings.MEDIA_ROOT
        self.addCleanup(shutil.rmtree, media_root, True)
        self.client.force_authenticate(user=self.admin)
        response = self.post_upload(
            "notes.pdf", b"%PDF-1.4 oversized", "application/pdf",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)
