"""Read-only OneRoster groundwork: HS256 assertions, scoping and rejections."""
import base64
import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import ContentStatus, Roles
from apps.core.models import AuditLog
from apps.courses.models import Course, Lesson, LessonProgress, Module
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner
from apps.teachers.models import Teacher

User = get_user_model()
CLIENT_ID = "sis-client"
SECRET = "integration-test-secret"
ALL_SCOPES = [
    "courses.read", "classes.read", "users.read",
    "enrollments.read", "orgs.read",
]


def _b64(value):
    return base64.urlsafe_b64encode(
        json.dumps(value, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")


def make_assertion(
    client_id=CLIENT_ID, secret=SECRET, scopes=None, algorithm="HS256",
    audience="klb-lms-oneroster", lifetime=300, expired=False,
):
    now = int(time.time())
    issued = now - 400 if expired else now
    expires = now - 100 if expired else now + lifetime
    header = {"alg": algorithm, "typ": "JWT"}
    claims = {
        "iss": client_id,
        "sub": client_id,
        "aud": audience,
        "iat": issued,
        "exp": expires,
        "jti": "integration-test-assertion",
    }
    signing_input = f"{_b64(header)}.{_b64(claims)}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    suffix = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{signing_input.decode('ascii')}.{suffix}"


class OneRosterTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Integration Type", code="INTT")
        self.school = Institution.objects.create(
            name="Integration School", code="INTSCH", institution_type=kind
        )
        self.other_school = Institution.objects.create(
            name="Other Integration School", code="INTOUT", institution_type=kind
        )
        teacher_user = User.objects.create_user(
            username="integration_teacher", role=Roles.TEACHER,
            institution=self.school, first_name="Wanjiku", last_name="Kamau",
            email="teacher@example.invalid",
        )
        self.teacher = Teacher.objects.create(
            institution=self.school, user=teacher_user, staff_number="INT-T1"
        )
        learner_user = User.objects.create_user(
            username="integration_learner", role=Roles.LEARNER,
            institution=self.school, first_name="Amina", last_name="Ali",
        )
        self.learner = Learner.objects.create(
            institution=self.school, user=learner_user, admission_number="INT-L1"
        )
        other_user = User.objects.create_user(
            username="integration_other", role=Roles.LEARNER,
            institution=self.other_school, first_name="Other", last_name="Learner",
        )
        self.other_learner = Learner.objects.create(
            institution=self.other_school, user=other_user,
            admission_number="INT-OTHER",
        )
        self.course = Course.objects.create(
            institution=self.school, title="Grade 7 Mathematics",
            code="INT-CRS-1", teacher=self.teacher, status=ContentStatus.PUBLISHED,
        )
        Course.objects.create(
            institution=self.school, title="Draft Mathematics",
            code="INT-DRAFT", status=ContentStatus.DRAFT,
        )
        Course.objects.create(
            institution=self.other_school, title="Other School Mathematics",
            code="INT-OTHER-CRS", status=ContentStatus.PUBLISHED,
        )
        module = Module.objects.create(
            institution=self.school, course=self.course, title="Numbers", sequence=1
        )
        lesson = Lesson.objects.create(
            institution=self.school, module=module, title="Whole numbers", sequence=1
        )
        LessonProgress.objects.create(
            institution=self.school, learner=self.learner, lesson=lesson,
            status="IN_PROGRESS",
        )

    def client_config(self, scopes=None):
        return json.dumps({
            CLIENT_ID: {
                "secret": SECRET,
                "institution_id": self.school.pk,
                "scopes": scopes or ALL_SCOPES,
            }
        })

    def auth(self, **kwargs):
        return {"HTTP_AUTHORIZATION": f"Bearer {make_assertion(**kwargs)}"}

    def get(self, name, scopes=None, query=None, **auth_kwargs):
        with override_settings(ONEROSTER_CLIENTS_JSON=self.client_config(scopes)):
            return self.client.get(
                reverse(name), query or {}, **self.auth(**auth_kwargs)
            )

    def test_published_courses_are_pinned_and_audited_without_secrets(self):
        response = self.get("oneroster-courses")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            [row["title"] for row in response.data["courses"]],
            ["Grade 7 Mathematics"],
        )
        self.assertEqual(response.data["paging"]["total"], 1)
        self.assertEqual(response.data["courses"][0]["orgSourcedId"], self.school.code)

        audit = AuditLog.objects.get(action="integration.oneroster.read")
        self.assertIsNone(audit.user_id)
        self.assertEqual(audit.institution_id, self.school.pk)
        self.assertEqual(audit.entity_id, "courses")
        self.assertEqual(audit.details["client_id"], CLIENT_ID)
        self.assertEqual(audit.details["scope"], "courses.read")
        self.assertNotIn(SECRET, str(audit.details))
        self.assertNotIn(SECRET, str(response.data))

    def test_each_resource_requires_its_own_scope(self):
        limited = ["courses.read"]
        response = self.get("oneroster-courses", scopes=limited)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        for name in ("oneroster-classes", "oneroster-users", "oneroster-enrollments", "oneroster-orgs"):
            with self.subTest(endpoint=name):
                denied = self.get(name, scopes=limited)
                self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_and_enrollments_stay_inside_the_pinned_school(self):
        users = self.get("oneroster-users")
        self.assertEqual(users.status_code, status.HTTP_200_OK, users.data)
        self.assertEqual(users.data["paging"]["total"], 2)
        roles = {row["role"] for row in users.data["users"]}
        self.assertEqual(roles, {"student", "teacher"})
        self.assertTrue(all(row["orgSourcedId"] == self.school.code for row in users.data["users"]))
        self.assertFalse(any("Other" in str(row) for row in users.data["users"]))

        enrollments = self.get("oneroster-enrollments")
        self.assertEqual(enrollments.status_code, status.HTTP_200_OK, enrollments.data)
        roles = {row["role"] for row in enrollments.data["enrollments"]}
        self.assertEqual(roles, {"student", "teacher"})
        self.assertTrue(all(
            row["classSourcedId"] == self.course.code
            for row in enrollments.data["enrollments"]
        ))

    def test_rs256_expired_and_missing_assertions_are_refused(self):
        with override_settings(ONEROSTER_CLIENTS_JSON=self.client_config()):
            algorithm = self.client.get(
                reverse("oneroster-courses"),
                **{"HTTP_AUTHORIZATION": f"Bearer {make_assertion(algorithm='RS256')}"},
            )
            self.assertEqual(algorithm.status_code, status.HTTP_401_UNAUTHORIZED)
            expired = self.client.get(
                reverse("oneroster-courses"),
                **{"HTTP_AUTHORIZATION": f"Bearer {make_assertion(expired=True)}"},
            )
            self.assertEqual(expired.status_code, status.HTTP_401_UNAUTHORIZED)
            missing = self.client.get(reverse("oneroster-courses"))
            self.assertEqual(missing.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertIn("Bearer", missing["WWW-Authenticate"])
        self.assertFalse(AuditLog.objects.filter(action="integration.oneroster.read").exists())

    def test_writes_and_unsupported_protocol_endpoints_are_closed(self):
        with override_settings(ONEROSTER_CLIENTS_JSON=self.client_config()):
            response = self.client.post(
                reverse("oneroster-courses"), {}, format="json", **self.auth()
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        for name in (
            "integration-lti-unsupported", "integration-oidc-unsupported",
            "integration-jwks-unsupported", "integration-oauth-unsupported",
        ):
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(response.data["code"], "unsupported_integration")
        self.assertEqual(
            AuditLog.objects.filter(action="integration.unsupported.rejected").count(), 4
        )

    def test_paging_is_bounded_by_operator_configuration(self):
        Course.objects.create(
            institution=self.school, title="More Mathematics",
            code="INT-CRS-2", status=ContentStatus.PUBLISHED,
        )
        response = self.get("oneroster-courses", query={"limit": "1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["courses"]), 1)
        self.assertEqual(response.data["paging"]["total"], 2)

        with override_settings(
            ONEROSTER_CLIENTS_JSON=self.client_config(), ONEROSTER_MAX_PAGE_SIZE=1
        ):
            capped = self.client.get(
                reverse("oneroster-courses"), {"limit": "50"}, **self.auth()
            )
        self.assertEqual(capped.data["paging"]["limit"], 1)
