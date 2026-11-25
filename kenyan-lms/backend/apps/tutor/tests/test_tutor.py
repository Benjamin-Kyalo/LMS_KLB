"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
import os
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.content.models import Chapter, ContentResource, DigitalTextbook, Publisher
from apps.core.constants import Roles
from apps.courses.models import Course
from apps.guardians.models import Guardian
from apps.curriculum.models import (
    Competency, CurriculumFramework, EducationLevel, LearningArea,
    LearningOutcome, Strand, SubStrand,
)
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian
from apps.tutor.models import TutorConversation, TutorMessage
from apps.tutor.service import get_provider

User = get_user_model()
OUTCOME_TEXT = "Represent and compare whole numbers up to 10,000."


class TutorTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        kind = InstitutionType.objects.create(name="Tutor Test Type", code="TUTT")
        spare_school = Institution.objects.create(
            name="Tutor School A", code="TUTA", institution_type=kind,
        )
        # Reuse the seeded demo accounts; create them only if the test database
        # has no demo data. No password is supplied or printed either way.
        self.admin = self._user("demo_admin", Roles.ADMIN, spare_school)
        self.school = self.admin.institution or spare_school
        if self.admin.institution_id is None:
            self.admin.institution = self.school
            self.admin.save(update_fields=["institution"])
        self.other = Institution.objects.create(
            name="Tutor School B", code="TUTB", institution_type=kind,
        )
        self.other_user = self._user("demo_teacher", Roles.TEACHER, self.other)
        self.learner_user = self._user("demo_learner", Roles.LEARNER, self.school)

        self.learner, _ = Learner.objects.get_or_create(
            user=self.learner_user,
            defaults={"institution": self.school, "admission_number": "TUT-L1"},
        )
        if self.learner.institution_id != self.school.pk:
            self.learner.institution = self.school
            self.learner.save(update_fields=["institution"])
        self.conversation = TutorConversation.objects.create(
            institution=self.school,
            title="Whole numbers help",
            learner=self.learner,
            started_by=self.admin,
        )
        self._create_curriculum()

    def _user(self, username, role, institution=None):
        user = User.objects.filter(username=username).first()
        if user is None:
            return User.objects.create_user(
                username=username, password=None, role=role, institution=institution,
            )
        if institution is not None and user.institution_id != institution.pk:
            user.institution = institution
            user.save(update_fields=["institution"])
        return user

    def _create_curriculum(self):
        framework = CurriculumFramework.objects.create(
            name="Tutor Test Framework", code="TUTFW-T", version="1",
        )
        level = EducationLevel.objects.create(
            framework=framework, name="Primary", code="TUTPRI",
        )
        area = LearningArea.objects.create(level=level, name="Mathematics", code="TUTMAT")
        strand = Strand.objects.create(learning_area=area, name="Numbers", code="TUTNUM")
        sub_strand = SubStrand.objects.create(strand=strand, name="Whole numbers", code="TUTWN")
        self.outcome = LearningOutcome.objects.create(
            sub_strand=sub_strand, code="TUT-LO-1", description=OUTCOME_TEXT,
        )
        Competency.objects.create(
            framework=framework, name="Critical thinking", code="TUT-CT",
            description="Think critically about whole numbers.",
        )
        publisher = Publisher.objects.create(name="Tutor Test Publisher", code="TUTPUB")
        textbook = DigitalTextbook.objects.create(
            publisher=publisher, title="Mathematics 4", isbn="TUT-TB-1",
            description="A textbook about whole numbers.",
        )
        chapter = Chapter.objects.create(textbook=textbook, title="Numbers", chapter_number=1)
        ContentResource.objects.create(
            chapter=chapter, title="Whole numbers video",
            description="Explains whole numbers.", resource_type="VIDEO",
        )
        Course.objects.create(
            institution=self.school, title="Grade 4 Mathematics", code="TUT-CRS-1",
            description="Practice whole numbers.", status="PUBLISHED",
        )

    def test_list_endpoints_are_institution_scoped(self):
        TutorMessage.objects.create(
            institution=self.school, conversation=self.conversation,
            role=TutorMessage.Role.USER, body="A private question", created_by=self.admin,
        )
        self.client.force_authenticate(user=self.other_user)
        for name in ("tutorconversation-list", "tutormessage-list"):
            with self.subTest(endpoint=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
                self.assertEqual(response.data["results"], [])

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("tutormessage-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_ask_persists_messages_and_answers_from_stored_text(self):
        self.client.force_authenticate(user=self.admin)
        with patch("apps.tutor.service._open_url", side_effect=AssertionError("network")) as remote:
            response = self.client.post(
                reverse("tutorconversation-ask", args=[self.conversation.pk]),
                {"question": "Explain whole numbers up to 10,000"},
                format="json",
            )
        remote.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["role"], TutorMessage.Role.TUTOR)
        self.assertTrue(response.data["grounded"])
        self.assertTrue(response.data["sources"])
        self.assertIn(OUTCOME_TEXT, response.data["answer"])
        self.assertIn("Learning outcome", response.data["source_labels"][0])
        self.assertNotIn("http", response.data["answer"].lower())

        question_message = self.conversation.messages.get(role=TutorMessage.Role.USER)
        answer_message = self.conversation.messages.get(role=TutorMessage.Role.TUTOR)
        self.assertEqual(question_message.body, "Explain whole numbers up to 10,000")
        self.assertEqual(answer_message.body, response.data["answer"])
        self.assertEqual(answer_message.institution_id, self.school.pk)

    def test_unrelated_question_returns_fallback_without_network(self):
        self.client.force_authenticate(user=self.admin)
        with patch("apps.tutor.service._open_url", side_effect=AssertionError("network")) as remote:
            response = self.client.post(
                reverse("tutorconversation-ask", args=[self.conversation.pk]),
                {"question": "Hello there, how are you?"},
                format="json",
            )
        remote.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertFalse(response.data["grounded"])
        self.assertEqual(response.data["sources"], [])
        self.assertIn("could not find", response.data["answer"])

    def test_http_provider_without_configuration_stays_local(self):
        with patch.dict(os.environ, {"KLB_TUTOR_PROVIDER": "local"}, clear=False):
            self.assertEqual(get_provider().name, "local")
        with patch.dict(os.environ, {"KLB_TUTOR_PROVIDER": "http"}, clear=False):
            os.environ.pop("KLB_TUTOR_API_URL", None)
            os.environ.pop("KLB_TUTOR_API_KEY", None)
            provider = get_provider()
            self.assertEqual(provider.name, "http")
            with patch("apps.tutor.service._open_url", side_effect=AssertionError("network")) as remote:
                result = provider.answer("Explain whole numbers up to 10,000", self.school)
            remote.assert_not_called()
            self.assertTrue(result["grounded"])

    def test_http_provider_refuses_non_https_and_unlisted_hosts(self):
        with patch.dict(os.environ, {
            "KLB_TUTOR_PROVIDER": "http",
            "KLB_TUTOR_API_URL": "http://tutor.example.invalid/answer",
            "KLB_TUTOR_API_KEY": "never-a-real-key",
            "KLB_TUTOR_ALLOWED_HOSTS": "tutor.example.invalid",
        }, clear=False), patch(
            "apps.tutor.service._open_url", side_effect=AssertionError("network")
        ) as remote:
            result = get_provider().answer("Explain whole numbers up to 10,000", self.school)
        remote.assert_not_called()
        self.assertTrue(result["grounded"])

        with patch.dict(os.environ, {
            "KLB_TUTOR_PROVIDER": "http",
            "KLB_TUTOR_API_URL": "https://other.example.invalid/answer",
            "KLB_TUTOR_API_KEY": "never-a-real-key",
            "KLB_TUTOR_ALLOWED_HOSTS": "tutor.example.invalid",
        }, clear=False), patch(
            "apps.tutor.service._open_url", side_effect=AssertionError("network")
        ) as remote:
            result = get_provider().answer("Explain whole numbers up to 10,000", self.school)
        remote.assert_not_called()
        self.assertTrue(result["grounded"])

    def test_http_provider_fails_closed_on_redirect(self):
        with patch.dict(os.environ, {
            "KLB_TUTOR_PROVIDER": "http",
            "KLB_TUTOR_API_URL": "https://tutor.example.invalid/answer",
            "KLB_TUTOR_API_KEY": "never-a-real-key",
            "KLB_TUTOR_ALLOWED_HOSTS": "tutor.example.invalid",
        }, clear=False), patch(
            "apps.tutor.service._open_url", side_effect=URLError("redirect refused")
        ) as remote:
            result = get_provider().answer("Explain whole numbers up to 10,000", self.school)
        remote.assert_called_once()
        self.assertTrue(result["grounded"])

    def test_question_is_sanitised_before_it_is_stored(self):
        self.client.force_authenticate(user=self.admin)
        with patch("apps.tutor.service._open_url", side_effect=AssertionError("network")):
            response = self.client.post(
                reverse("tutorconversation-ask", args=[self.conversation.pk]),
                {"question": "\x00Explain whole\x01 numbers up to 10,000   "},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        question_message = self.conversation.messages.get(role=TutorMessage.Role.USER)
        self.assertEqual(question_message.body, "Explain whole numbers up to 10,000")

    def test_health_reports_provider_without_configuration_values(self):
        self.client.force_authenticate(user=self.admin)
        dummy_key = "never-a-real-key"
        dummy_url = "https://example.invalid/tutor"
        with patch.dict(os.environ, {
            "KLB_TUTOR_PROVIDER": "http",
            "KLB_TUTOR_API_URL": dummy_url,
            "KLB_TUTOR_API_KEY": dummy_key,
        }, clear=False):
            response = self.client.get(reverse("tutorconversation-health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["provider"], "http")
        self.assertTrue(response.data["grounded_only"])
        self.assertNotIn(dummy_key, str(response.data))
        self.assertNotIn(dummy_url, str(response.data))

    def _extra_learner(self, username, admission_number):
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username, password=None,
                role=Roles.LEARNER, institution=self.school,
            )
        learner, _ = Learner.objects.get_or_create(
            user=user,
            defaults={
                "institution": self.school,
                "admission_number": admission_number,
            },
        )
        return learner

    def _guardian(self, username):
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username, password=None,
                role=Roles.GUARDIAN, institution=self.school,
            )
        guardian, _ = Guardian.objects.get_or_create(
            user=user, defaults={"institution": self.school}
        )
        return guardian

    def test_learner_can_create_conversation_and_ask_about_own_record(self):
        self.client.force_authenticate(user=self.learner_user)
        response = self.client.post(
            reverse("tutorconversation-list"),
            {"title": "My fractions practice"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = TutorConversation.objects.get(pk=response.data["id"])
        self.assertEqual(created.started_by_id, self.learner_user.pk)
        self.assertEqual(created.learner_id, self.learner.pk)
        self.assertEqual(created.institution_id, self.school.pk)

        with patch("apps.tutor.service._open_url", side_effect=AssertionError("network")):
            answer = self.client.post(
                reverse("tutorconversation-ask", args=[created.pk]),
                {"question": OUTCOME_TEXT},
                format="json",
            )
        self.assertEqual(answer.status_code, status.HTTP_201_CREATED, answer.data)
        self.assertEqual(answer.data["role"], TutorMessage.Role.TUTOR)

    def test_learner_cannot_use_another_learners_record_or_conversation(self):
        other_learner = self._extra_learner("tutor_other_learner", "TUT-L2")
        other_conversation = TutorConversation.objects.create(
            institution=self.school,
            title="Another learner's thread",
            learner=other_learner,
            started_by=self.admin,
        )
        self.client.force_authenticate(user=self.learner_user)

        rejected = self.client.post(
            reverse("tutorconversation-list"),
            {"title": "Not mine", "learner": other_learner.pk},
            format="json",
        )
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST, rejected.data)

        visible = self.client.get(reverse("tutorconversation-list"))
        self.assertEqual(visible.status_code, status.HTTP_200_OK, visible.data)
        ids = [row["id"] for row in visible.data["results"]]
        self.assertIn(self.conversation.pk, ids)
        self.assertNotIn(other_conversation.pk, ids)

        asked = self.client.post(
            reverse("tutorconversation-ask", args=[other_conversation.pk]),
            {"question": OUTCOME_TEXT},
            format="json",
        )
        self.assertEqual(asked.status_code, status.HTTP_404_NOT_FOUND, asked.data)

    def test_guardian_can_use_linked_learner_but_not_unlinked_records(self):
        guardian = self._guardian("tutor_guardian_a")
        LearnerGuardian.objects.get_or_create(
            learner=self.learner, guardian=guardian,
            defaults={"relationship": "Mother", "is_primary": True},
        )
        other_learner = self._extra_learner("tutor_unlinked_learner", "TUT-L3")
        other_conversation = TutorConversation.objects.create(
            institution=self.school,
            title="Unlinked thread",
            learner=other_learner,
            started_by=self.admin,
        )
        self.client.force_authenticate(user=guardian.user)

        created = self.client.post(
            reverse("tutorconversation-list"),
            {"title": "Question about my child"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        conversation = TutorConversation.objects.get(pk=created.data["id"])
        self.assertEqual(conversation.learner_id, self.learner.pk)
        self.assertEqual(conversation.started_by_id, guardian.user.pk)

        visible = self.client.get(reverse("tutorconversation-list"))
        ids = [row["id"] for row in visible.data["results"]]
        self.assertIn(conversation.pk, ids)
        self.assertIn(self.conversation.pk, ids)
        self.assertNotIn(other_conversation.pk, ids)

        asked = self.client.post(
            reverse("tutorconversation-ask", args=[other_conversation.pk]),
            {"question": OUTCOME_TEXT},
            format="json",
        )
        self.assertEqual(asked.status_code, status.HTTP_404_NOT_FOUND, asked.data)

    def test_anonymous_users_cannot_use_tutor_endpoints(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("tutorconversation-list"))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
