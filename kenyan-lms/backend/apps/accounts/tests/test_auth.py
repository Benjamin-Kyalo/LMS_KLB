"""Tests for login, registration and permission rules."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.institutions.models import Institution, InstitutionType

User = get_user_model()


class AuthenticationTests(APITestCase):
    def test_login_returns_token(self):
        User.objects.create_user(username="admin", password="StrongPass123!", role=Roles.SCHOOL_ADMIN)
        response = self.client.post(reverse("login"), {"username": "admin", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["role"], Roles.SCHOOL_ADMIN)

    def test_login_rejects_bad_password(self):
        User.objects.create_user(username="admin", password="StrongPass123!")
        response = self.client.post(reverse("login"), {"username": "admin", "password": "wrong"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_read_own_profile(self):
        user = User.objects.create_user(username="teacher", password="StrongPass123!", role=Roles.TEACHER)
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "teacher")

    def test_profile_includes_school_identity(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI2")
        school = Institution.objects.create(name="School A", code="A2", institution_type=kind)
        user = User.objects.create_user(
            username="schooluser", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=school,
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["institution_name"], "School A")
        self.assertIn("institution_logo", response.data)

    def test_teacher_cannot_create_users(self):
        user = User.objects.create_user(username="teacher", password="StrongPass123!", role=Roles.TEACHER)
        self.client.force_authenticate(user=user)
        response = self.client.post(reverse("user-list"), {
            "username": "newuser", "password": "StrongPass123!", "role": Roles.LEARNER,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_platform_admin_can_list_roles(self):
        user = User.objects.create_user(username="root", password="StrongPass123!", role=Roles.SUPER_ADMIN)
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("user-roles"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(Roles.CHOICES))

    def test_create_superuser_defaults_to_platform_super_admin_role(self):
        user = User.objects.create_superuser(
            username="rootsuper", email="rootsuper@example.invalid", password="StrongPass123!"
        )
        self.assertEqual(user.role, Roles.SUPER_ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class InstitutionAssignmentTests(APITestCase):
    """A school user must never be able to choose another institution."""

    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(name="A", code="A1", institution_type=kind)
        self.other = Institution.objects.create(name="B", code="B1", institution_type=kind)
        self.admin = User.objects.create_user(
            username="admin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )

    def test_cannot_create_user_in_another_institution(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("user-list"), {
            "username": "smuggled", "password": "StrongPass123!",
            "first_name": "S", "last_name": "M", "role": Roles.TEACHER,
            "institution": self.other.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(User.objects.get(username="smuggled").institution_id, self.school.id)

    def test_cannot_move_user_to_another_institution(self):
        target = User.objects.create_user(
            username="target", password="StrongPass123!",
            role=Roles.TEACHER, institution=self.school,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("user-detail", args=[target.id]),
            {"institution": self.other.id}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        target.refresh_from_db()
        self.assertEqual(target.institution_id, self.school.id)


class RegistrationTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Sample Primary", code="SMPR")
        self.school = Institution.objects.create(name="Sample School", code="SMPS", institution_type=kind)

    def test_learner_can_self_register_with_role_specific_fields(self):
        response = self.client.post(reverse("register"), {
            "username": "newlearner", "email": "newlearner@sample.invalid",
            "password": "StrongPass123!", "first_name": "New", "last_name": "Learner",
            "role": Roles.LEARNER, "institution": self.school.id,
            "date_of_birth": "2015-06-01", "gender": "F",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(username="newlearner")
        self.assertEqual(user.role, Roles.LEARNER)
        self.assertTrue(user.learner_profile)
        self.assertTrue(user.is_active)

    def test_teacher_registration_is_pending_approval(self):
        response = self.client.post(reverse("register"), {
            "username": "newteacher", "email": "newteacher@sample.invalid",
            "password": "StrongPass123!", "first_name": "New", "last_name": "Teacher",
            "role": Roles.TEACHER, "institution": self.school.id,
            "employment_type": "CONTRACT",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(username="newteacher")
        self.assertEqual(user.role, Roles.TEACHER)
        self.assertFalse(user.is_active)
        self.assertTrue(user.teacher_profile)

    def test_public_registration_rejects_admin_role(self):
        response = self.client.post(reverse("register"), {
            "username": "eviladmin", "email": "evil@sample.invalid",
            "password": "StrongPass123!", "first_name": "Evil", "last_name": "Admin",
            "role": Roles.SCHOOL_ADMIN, "institution": self.school.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_public_registration_is_rejected(self):
        payload = {
            "username": "duplicate", "email": "duplicate@sample.invalid",
            "password": "StrongPass123!", "first_name": "Dup", "last_name": "Licate",
            "role": Roles.LEARNER, "institution": self.school.id,
            "date_of_birth": "2014-01-01", "gender": "M",
        }
        self.assertEqual(self.client.post(reverse("register"), payload, format="json").status_code,
                         status.HTTP_201_CREATED)
        payload["email"] = "other@sample.invalid"
        response = self.client.post(reverse("register"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_school_admin_cannot_grant_platform_role(self):
        admin = User.objects.create_user(
            username="schooladmin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )
        self.client.force_authenticate(user=admin)
        response = self.client.post(reverse("user-list"), {
            "username": "promoted", "email": "promoted@sample.invalid",
            "password": "StrongPass123!", "role": Roles.SUPER_ADMIN,
            "institution": self.school.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_learner_cannot_change_school_profile(self):
        learner = User.objects.create_user(
            username="learnerx", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.client.force_authenticate(user=learner)
        response = self.client.patch(reverse("institution-detail", args=[self.school.id]),
                                     {"motto": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_learner_cannot_create_classes(self):
        learner = User.objects.create_user(
            username="learnerclass", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.client.force_authenticate(user=learner)
        response = self.client.post(reverse("schoolclass-list"), {
            "institution": self.school.id, "academic_year": 1, "name": "Grade 9", "stream": "A",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminInvitationTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Invite Primary", code="INVP")
        self.school = Institution.objects.create(name="Invite School", code="INVS", institution_type=kind)
        self.super_admin = User.objects.create_superuser(
            username="inviter", email="inviter@sample.invalid", password="StrongPass123!"
        )

    def test_invitation_is_single_use_and_creates_admin(self):
        self.client.force_authenticate(user=self.super_admin)
        created = self.client.post(reverse("admin-invitation-list"), {
            "email": "newadmin@sample.invalid", "role": Roles.SCHOOL_ADMIN,
            "institution": self.school.id,
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)

        self.client.force_authenticate(user=None)
        accepted = self.client.post(reverse("admin-invitation-accept"), {
            "token": created.data["token"], "username": "newadmin",
            "email": "newadmin@sample.invalid", "first_name": "New", "last_name": "Admin",
            "password": "StrongPass123!",
        }, format="json")
        self.assertEqual(accepted.status_code, status.HTTP_201_CREATED, accepted.data)
        self.assertEqual(User.objects.get(username="newadmin").role, Roles.SCHOOL_ADMIN)

        reused = self.client.post(reverse("admin-invitation-accept"), {
            "token": created.data["token"], "username": "newadmin2",
            "email": "newadmin@sample.invalid", "first_name": "New", "last_name": "Admin2",
            "password": "StrongPass123!",
        }, format="json")
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_issue_invitation(self):
        learner = User.objects.create_user(
            username="invitelearner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.client.force_authenticate(user=learner)
        response = self.client.post(reverse("admin-invitation-list"), {
            "email": "hacker@sample.invalid", "role": Roles.SCHOOL_ADMIN,
            "institution": self.school.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_admin_cannot_invite_into_another_institution(self):
        other_kind = InstitutionType.objects.create(name="Other Invite", code="OTH")
        other_school = Institution.objects.create(
            name="Other School", code="OTHS", institution_type=other_kind
        )
        admin = User.objects.create_user(
            username="localadmin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )
        self.client.force_authenticate(user=admin)
        response = self.client.post(reverse("admin-invitation-list"), {
            "email": "cross@sample.invalid", "role": Roles.SCHOOL_ADMIN,
            "institution": other_school.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
