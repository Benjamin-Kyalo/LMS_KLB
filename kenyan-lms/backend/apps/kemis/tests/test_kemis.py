"""Automated checks for the local KEMIS-style staging endpoints.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
import json
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessments.models import Exam, ExamResult
from apps.attendance.models import AttendanceRecord
from apps.core.constants import Roles
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass
from apps.kemis.builders import build_rows
from apps.kemis.models import KemisExport, KemisFieldMapping
from apps.learners.models import Learner
from apps.teachers.models import Teacher

User = get_user_model()
DATASETS = {"LEARNERS", "TEACHERS", "INSTITUTION", "ENROLLMENT", "ATTENDANCE", "RESULTS"}


class KemisTestBase(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="KEMIS Demo Type")
        self.school = Institution.objects.create(
            name="KEMIS Demo School", code="KEM001", institution_type=self.kind,
        )
        self.other_school = Institution.objects.create(
            name="KEMIS Other School", code="KEM002", institution_type=self.kind,
        )
        # Only the seeded demo usernames are used. No password is set or printed.
        self.admin = self._demo_user("demo_admin", Roles.SCHOOL_ADMIN, self.school)
        self.teacher = self._demo_user("demo_teacher", Roles.TEACHER, self.school)
        self.learner_user = self._demo_user("demo_learner", Roles.LEARNER, self.school)
        self.guardian = self._demo_user("demo_guardian", Roles.GUARDIAN, self.school)
        self.platform = self._demo_user("platform_admin", Roles.SUPER_ADMIN, None)

    @staticmethod
    def _demo_user(username, role, institution):
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username, password=None, role=role, institution=institution,
            )
        else:
            user.role = role
            user.institution = institution
            user.save(update_fields=["role", "institution"])
        return user

    def _create_sample_records(self):
        year = AcademicYear.objects.create(
            institution=self.school, name="2026",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        klass = SchoolClass.objects.create(
            institution=self.school, academic_year=year, name="Grade 4",
            level="PRIMARY", stream="A",
        )
        Teacher.objects.create(user=self.teacher, institution=self.school, staff_number="KEM-T1")
        learner = Learner.objects.create(
            user=self.learner_user, institution=self.school,
            admission_number="KEM-L1", class_room=klass,
        )
        AttendanceRecord.objects.create(
            learner=learner, institution=self.school, date=date(2026, 3, 1), status="PRESENT",
        )
        exam = Exam.objects.create(
            title="Mathematics", institution=self.school, exam_date=date(2026, 3, 2),
        )
        ExamResult.objects.create(
            exam=exam, learner=learner, institution=self.school, score=81,
        )
        return klass, learner


class KemisExportEndpointTests(KemisTestBase):
    def test_export_list_is_institution_scoped(self):
        own = KemisExport.objects.create(
            institution=self.school, dataset="LEARNERS", format="CSV", status="READY",
        )
        other = KemisExport.objects.create(
            institution=self.other_school, dataset="LEARNERS", format="CSV", status="READY",
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("kemisexport-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [own.id])
        self.assertNotIn(other.id, ids)

        self.client.force_authenticate(user=self.platform)
        response = self.client.get(reverse("kemisexport-list"))
        self.assertEqual(len(response.data["results"]), 2)

    def test_non_staff_writes_are_forbidden_and_teacher_write_is_scoped(self):
        body = {"dataset": "LEARNERS", "format": "CSV", "notes": "local staging"}
        self.client.force_authenticate(user=self.learner_user)
        self.assertEqual(
            self.client.post(reverse("kemisexport-list"), body, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(user=self.guardian)
        self.assertEqual(
            self.client.post(reverse("kemisexport-list"), body, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(reverse("kemisexport-list"), body, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = KemisExport.objects.get(pk=response.data["id"])
        self.assertEqual(created.institution_id, self.school.id)
        self.assertTrue(created.reference.startswith("KEM-"))

    def test_generate_csv_then_download(self):
        _, learner = self._create_sample_records()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("kemisexport-generate"),
            {"dataset": "LEARNERS", "format": "CSV", "filters": {"status": "ACTIVE"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["status"], "READY")
        self.assertEqual(response.data["record_count"], 1)
        self.assertTrue(response.data["reference"].startswith("KEM-"))
        self.assertEqual(response.data["preview"][0][0], learner.admission_number)
        self.assertIn("ADMISSION_NUMBER", response.data["payload"])

        export = KemisExport.objects.get(pk=response.data["id"])
        self.assertEqual(export.generated_by_id, self.admin.id)
        self.assertIsNotNone(export.generated_at)

        download = self.client.get(reverse("kemisexport-download", args=[export.id]))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", download["Content-Disposition"])
        self.assertIn(b"ADMISSION_NUMBER", download.content)
        self.assertIn(learner.admission_number.encode(), download.content)

    def test_generate_json_then_download(self):
        self._create_sample_records()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("kemisexport-generate"),
            {"dataset": "RESULTS", "format": "JSON"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        download = self.client.get(
            reverse("kemisexport-download", args=[response.data["id"]])
        )
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertTrue(download["Content-Type"].startswith("application/json"))
        payload = json.loads(download.content)
        self.assertEqual(payload["dataset"], "RESULTS")
        self.assertEqual(payload["record_count"], 1)
        self.assertIn("SCORE", payload["columns"])

        other_download = self.client.get(
            reverse("kemisexport-download", args=[self._other_export().id])
        )
        self.assertEqual(other_download.status_code, status.HTTP_404_NOT_FOUND)

    def _other_export(self):
        return KemisExport.objects.create(
            institution=self.other_school, dataset="LEARNERS", format="CSV", status="READY",
        )

    def test_generate_validation(self):
        self.client.force_authenticate(user=self.admin)
        invalid = self.client.post(
            reverse("kemisexport-generate"),
            {"dataset": "NOT_A_DATASET", "format": "CSV"}, format="json",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.platform)
        no_school = self.client.post(
            reverse("kemisexport-generate"),
            {"dataset": "LEARNERS", "format": "CSV"}, format="json",
        )
        self.assertEqual(no_school.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("institution", str(no_school.data))

    def test_datasets_endpoint_lists_defaults_and_active_mappings(self):
        KemisFieldMapping.objects.create(
            dataset="LEARNERS", source_field="user.full_name",
            target_column="LEARNER_NAME", is_required=True, ordering=1,
        )
        KemisFieldMapping.objects.create(
            dataset="LEARNERS", source_field="gender",
            target_column="SEX", is_active=False, ordering=2,
        )
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("kemisexport-datasets"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        datasets = {item["dataset"]: item for item in response.data}
        self.assertEqual(set(datasets), DATASETS)
        self.assertTrue(
            any(
                column["target_column"] == "ADMISSION_NUMBER"
                for column in datasets["LEARNERS"]["default_columns"]
            )
        )
        self.assertTrue(
            any(
                column["target_column"] == "LEARNER_NAME" and column["is_required"]
                for column in datasets["LEARNERS"]["mapped_columns"]
            )
        )
        self.assertFalse(
            any(
                column["target_column"] == "SEX"
                for column in datasets["LEARNERS"]["mapped_columns"]
            )
        )


class KemisFieldMappingEndpointTests(KemisTestBase):
    def test_list_works_for_authenticated_users(self):
        KemisFieldMapping.objects.create(
            dataset="TEACHERS", source_field="staff_number", target_column="STAFF_NUMBER",
        )
        for user in (self.admin, self.teacher, self.learner_user, self.guardian, self.platform):
            self.client.force_authenticate(user=user)
            response = self.client.get(reverse("kemisfieldmapping-list"))
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_writes_require_platform_admin(self):
        body = {
            "dataset": "LEARNERS", "source_field": "admission_number",
            "target_column": "ADMISSION_NUMBER",
        }
        for user in (self.admin, self.teacher, self.learner_user, self.guardian):
            self.client.force_authenticate(user=user)
            response = self.client.post(reverse("kemisfieldmapping-list"), body, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.platform)
        response = self.client.post(reverse("kemisfieldmapping-list"), body, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(response.data["reference"].startswith("KFM-"))


class KemisBuilderTests(KemisTestBase):
    def test_all_datasets_build_with_local_defaults(self):
        self._create_sample_records()
        for dataset in sorted(DATASETS):
            headers, rows = build_rows(dataset, self.school, filters={})
            self.assertTrue(headers, dataset)
            self.assertIsInstance(rows, list, dataset)

    def test_explicit_mappings_use_safe_dotted_paths(self):
        _, learner = self._create_sample_records()
        mappings = [
            {"dataset": "LEARNERS", "source_field": "user.full_name", "target_column": "PUPIL"},
            {"dataset": "LEARNERS", "source_field": "__class__", "target_column": "BLOCKED"},
            {"dataset": "LEARNERS", "source_field": "missing.field", "target_column": "MISSING"},
            {"dataset": "LEARNERS", "source_field": "gender", "target_column": "SEX", "is_active": False},
            {"dataset": "TEACHERS", "source_field": "staff_number", "target_column": "WRONG_DATASET"},
        ]
        headers, rows = build_rows("LEARNERS", self.school, mappings=mappings)
        self.assertEqual(headers, ["PUPIL", "BLOCKED", "MISSING"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], self.learner_user.full_name)
        self.assertEqual(rows[0][1], "")
        self.assertEqual(rows[0][2], "")
        self.assertEqual(learner.admission_number, "KEM-L1")

    def test_filters_are_allowlisted(self):
        self._create_sample_records()
        headers, rows = build_rows(
            "LEARNERS", self.school, filters={"status": "TRANSFERRED", "unknown__lookup": "x"},
        )
        self.assertTrue(headers)
        self.assertEqual(rows, [])
