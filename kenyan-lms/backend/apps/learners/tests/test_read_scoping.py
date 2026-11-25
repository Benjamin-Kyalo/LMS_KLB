"""Role/object scoping for learner PII reads."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian

User = get_user_model()


def rows(response):
    data = response.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


class LearnerReadScopingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        kind = InstitutionType.objects.create(name="Scope Primary", code="SCP")
        cls.school = Institution.objects.create(
            name="Scope School", code="SCOPE", institution_type=kind
        )
        cls.other_school = Institution.objects.create(
            name="Other School", code="SCOPE2", institution_type=kind
        )
        cls.admin = User.objects.create_user(
            username="scope_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=cls.school,
        )
        cls.learner_user = User.objects.create_user(
            username="scope_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.learner = Learner.objects.create(
            user=cls.learner_user, institution=cls.school, admission_number="SCOPE-001"
        )
        cls.sibling_user = User.objects.create_user(
            username="scope_sibling", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.school,
        )
        cls.sibling = Learner.objects.create(
            user=cls.sibling_user, institution=cls.school, admission_number="SCOPE-002"
        )
        foreign_user = User.objects.create_user(
            username="scope_foreign", password="StrongPass123!",
            role=Roles.LEARNER, institution=cls.other_school,
        )
        cls.foreign_learner = Learner.objects.create(
            user=foreign_user, institution=cls.other_school, admission_number="SCOPE-999"
        )
        guardian_user = User.objects.create_user(
            username="scope_guardian", password="StrongPass123!",
            role=Roles.GUARDIAN, institution=cls.school,
        )
        cls.guardian_user = guardian_user
        cls.guardian = Guardian.objects.create(user=guardian_user, institution=cls.school)

    def test_staff_reads_are_institution_wide(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("learner-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in rows(response)}, {self.learner.id, self.sibling.id}
        )
        self.assertEqual(
            self.client.get(reverse("learner-detail", args=[self.foreign_learner.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_learner_only_reads_own_record(self):
        self.client.force_authenticate(self.learner_user)
        response = self.client.get(reverse("learner-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in rows(response)], [self.learner.id])
        self.assertEqual(
            self.client.get(reverse("learner-detail", args=[self.learner.id])).status_code,
            status.HTTP_200_OK,
        )
        for learner_id in (self.sibling.id, self.foreign_learner.id):
            self.assertEqual(
                self.client.get(reverse("learner-detail", args=[learner_id])).status_code,
                status.HTTP_404_NOT_FOUND,
            )
        # An explicit filter must not widen the object-level scope.
        filtered = self.client.get(
            reverse("learner-list"), {"institution": self.other_school.id}
        )
        self.assertEqual(rows(filtered), [])

    def test_guardian_sees_only_verified_permitted_links(self):
        link = LearnerGuardian.objects.create(
            learner=self.learner, guardian=self.guardian, is_verified=False
        )
        self.client.force_authenticate(self.guardian_user)
        self.assertEqual(rows(self.client.get(reverse("learner-list"))), [])
        self.assertEqual(
            self.client.get(reverse("learner-detail", args=[self.learner.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

        link.is_verified = True
        link.save(update_fields=["is_verified"])
        response = self.client.get(reverse("learner-list"))
        self.assertEqual([row["id"] for row in rows(response)], [self.learner.id])
        self.assertIn("admission_number", rows(response)[0])

        link.can_view_academics = False
        link.save(update_fields=["can_view_academics"])
        self.assertEqual(rows(self.client.get(reverse("learner-list"))), [])

        link.can_view_academics = True
        link.save(update_fields=["can_view_academics"])
        LearnerGuardian.objects.create(
            learner=self.sibling, guardian=self.guardian, is_verified=True
        )
        self.assertEqual(
            {row["id"] for row in rows(self.client.get(reverse("learner-list")))},
            {self.learner.id, self.sibling.id},
        )
        self.assertEqual(
            self.client.get(reverse("learner-detail", args=[self.foreign_learner.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unlinked_guardian_sees_no_learners(self):
        self.client.force_authenticate(self.guardian_user)
        response = self.client.get(reverse("learner-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(rows(response), [])
