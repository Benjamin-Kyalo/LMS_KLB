"""Verified guardian link workflow tests."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import OnboardingProfile
from apps.core.constants import Roles
from apps.core.models import AuditLog
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import GuardianLinkRequest, Learner, LearnerGuardian

User = get_user_model()


class GuardianLinkRequestTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Link Primary", code="LNK")
        self.school = Institution.objects.create(name="Link School", code="LKS", institution_type=kind)
        self.other_school = Institution.objects.create(name="Other School", code="LKO", institution_type=kind)
        self.admin = User.objects.create_user(
            username="link_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school,
        )
        self.other_admin = User.objects.create_user(
            username="link_other_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.other_school,
        )
        guardian_user = User.objects.create_user(
            username="link_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=self.school,
        )
        self.guardian = Guardian.objects.create(
            user=guardian_user, institution=self.school, relationship_to_learner="Parent"
        )
        self.guardian_user = guardian_user
        learner_user = User.objects.create_user(
            username="link_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.learner = Learner.objects.create(
            user=learner_user, institution=self.school, admission_number="LNK-001"
        )
        self.profile = OnboardingProfile.objects.get(user=guardian_user)

    def _submit(self, user=None, identifier="LNK-001"):
        self.client.force_authenticate(user=user or self.guardian_user)
        return self.client.post(reverse("guardianlinkrequest-list"), {
            "learner_identifier": identifier, "relationship": "Parent",
        }, format="json")

    def test_guardian_can_request_a_link_without_gaining_access(self):
        response = self._submit()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        request = GuardianLinkRequest.objects.get()
        self.assertEqual(request.status, "PENDING")
        self.assertEqual(request.learner, self.learner)
        self.assertFalse(LearnerGuardian.objects.exists())
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.guardian_link_verified)

        links = self.client.get(reverse("report-my-learners"))
        self.assertEqual(links.data, [])

    def test_wrong_identifier_is_rejected(self):
        response = self._submit(identifier="NOPE")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("could not be linked", str(response.data["learner_identifier"]).lower())
        self.assertFalse(GuardianLinkRequest.objects.exists())

    def test_unknown_and_other_school_identifiers_look_identical(self):
        foreign_user = User.objects.create_user(
            username="link_foreign_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.other_school,
        )
        Learner.objects.create(
            user=foreign_user, institution=self.other_school, admission_number="OTHER-001"
        )
        unknown = self._submit(identifier="NOPE")
        elsewhere = self._submit(identifier="OTHER-001")
        self.assertEqual(unknown.status_code, elsewhere.status_code)
        self.assertEqual(unknown.data, elsewhere.data)
        self.assertNotIn("found at this school", str(elsewhere.data).lower())
        self.assertFalse(LearnerGuardian.objects.exists())

    def test_only_guardians_can_submit_requests(self):
        response = self._submit(user=self.admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_verification_creates_the_verified_grant(self):
        self.assertEqual(self._submit().status_code, status.HTTP_201_CREATED)
        link_request = GuardianLinkRequest.objects.get()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("guardianlinkrequest-verify", args=[link_request.id]), {
            "notes": "Admission number confirmed.", "is_primary": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        link_request.refresh_from_db()
        self.assertEqual(link_request.status, "VERIFIED")
        self.assertIsNotNone(link_request.verified_link)
        self.assertTrue(link_request.verified_link.is_verified)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.guardian_link_verified)

        links = self.client.get(reverse("report-my-learners"))
        self.assertEqual([row["id"] for row in links.data], [self.learner.id])
        self.assertTrue(AuditLog.objects.filter(
            action="verify", entity_type="GuardianLinkRequest", entity_id=str(link_request.id)
        ).exists())

    def test_verification_repairs_an_existing_unverified_link(self):
        self.assertEqual(self._submit().status_code, status.HTTP_201_CREATED)
        link_request = GuardianLinkRequest.objects.get()
        existing_link = LearnerGuardian.objects.create(
            learner=self.learner, guardian=self.guardian, is_verified=False,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("guardianlinkrequest-verify", args=[link_request.id]), {
            "notes": "Existing link confirmed.",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        existing_link.refresh_from_db()
        self.assertTrue(existing_link.is_verified)
        self.client.force_authenticate(user=self.guardian_user)
        links = self.client.get(reverse("report-my-learners"))
        self.assertEqual([row["id"] for row in links.data], [self.learner.id])

    def test_reject_requires_a_reason_and_creates_no_grant(self):
        self.assertEqual(self._submit().status_code, status.HTTP_201_CREATED)
        link_request = GuardianLinkRequest.objects.get()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("guardianlinkrequest-reject", args=[link_request.id]), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(reverse("guardianlinkrequest-reject", args=[link_request.id]), {
            "notes": "Identifier belongs to another learner.",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        link_request.refresh_from_db()
        self.assertEqual(link_request.status, "REJECTED")
        self.assertFalse(LearnerGuardian.objects.exists())

    def test_guardian_cannot_patch_request_status(self):
        self.assertEqual(self._submit().status_code, status.HTTP_201_CREATED)
        link_request = GuardianLinkRequest.objects.get()
        self.client.force_authenticate(user=self.guardian_user)
        response = self.client.patch(reverse("guardianlinkrequest-detail", args=[link_request.id]), {
            "status": "VERIFIED",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        link_request.refresh_from_db()
        self.assertEqual(link_request.status, "PENDING")

    def test_other_school_admin_cannot_verify(self):
        self.assertEqual(self._submit().status_code, status.HTTP_201_CREATED)
        link_request = GuardianLinkRequest.objects.get()
        self.client.force_authenticate(user=self.other_admin)
        response = self.client.post(reverse("guardianlinkrequest-verify", args=[link_request.id]), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        link_request.refresh_from_db()
        self.assertEqual(link_request.status, "PENDING")
