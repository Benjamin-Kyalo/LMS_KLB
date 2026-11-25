"""Teacher account approval workflow tests."""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import OnboardingProfile
from apps.core.constants import Roles
from apps.core.models import AuditLog
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass, Subject
from apps.teachers.models import Teacher, TeacherApproval, TeacherClassAssignment

User = get_user_model()


class TeacherApprovalTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Approval Primary", code="APP")
        self.school = Institution.objects.create(name="Approval School", code="APS", institution_type=kind)
        self.other_school = Institution.objects.create(name="Other School", code="APO", institution_type=kind)
        self.admin = User.objects.create_user(
            username="approval_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.school,
        )
        self.other_admin = User.objects.create_user(
            username="other_admin", password="StrongPass123!",
            role=Roles.ADMIN, institution=self.other_school,
        )
        self.teacher_user = User.objects.create_user(
            username="pending_teacher", password="StrongPass123!",
            role=Roles.TEACHER, institution=self.school, is_active=False,
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, institution=self.school,
            employment_type="CONTRACT", is_active=False,
        )
        self.approval = TeacherApproval.objects.create(
            institution=self.school, teacher=self.teacher, status="PENDING"
        )
        profile = OnboardingProfile.objects.get(user=self.teacher_user)
        profile.profile_complete = True
        profile.save(update_fields=["profile_complete"])
        self.year = AcademicYear.objects.create(
            institution=self.school, name="2026",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        self.subject = Subject.objects.create(institution=self.school, name="Mathematics", code="MATH")
        self.school_class = SchoolClass.objects.create(
            institution=self.school, academic_year=self.year, name="Grade 7", stream="A",
        )

    def test_only_institution_admins_can_review_pending_teachers(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("teacherapproval-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.approval.id])

        learner = User.objects.create_user(
            username="approval_learner", password="StrongPass123!",
            role=Roles.LEARNER, institution=self.school,
        )
        self.client.force_authenticate(user=learner)
        self.assertEqual(
            self.client.get(reverse("teacherapproval-list")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_approval_activates_account_and_can_assign_a_class(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("teacherapproval-approve", args=[self.approval.id]), {
            "school_class": self.school_class.id,
            "subject": self.subject.id,
            "academic_year": self.year.id,
            "is_class_teacher": True,
            "notes": "Verified employment details.",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.approval.refresh_from_db()
        self.teacher_user.refresh_from_db()
        self.teacher.refresh_from_db()
        self.assertEqual(self.approval.status, "APPROVED")
        self.assertEqual(self.approval.decided_by_id, self.admin.id)
        self.assertTrue(self.teacher_user.is_active)
        self.assertTrue(self.teacher.is_active)
        self.assertTrue(TeacherClassAssignment.objects.filter(teacher=self.teacher).exists())
        profile = OnboardingProfile.objects.get(user=self.teacher_user)
        self.assertTrue(profile.teacher_approved)
        self.assertTrue(profile.classes_assigned)
        self.assertTrue(profile.is_complete)
        self.assertIsNotNone(profile.completed_at)
        self.assertTrue(AuditLog.objects.filter(
            action="approve", entity_type="TeacherApproval", entity_id=str(self.approval.id)
        ).exists())

    def test_approval_without_assignment_leaves_class_step_open(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("teacherapproval-approve", args=[self.approval.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        profile = OnboardingProfile.objects.get(user=self.teacher_user)
        self.assertTrue(profile.teacher_approved)
        self.assertFalse(profile.classes_assigned)
        self.assertFalse(profile.is_complete)

    def test_partial_assignment_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("teacherapproval-approve", args=[self.approval.id]), {
            "school_class": self.school_class.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, "PENDING")

    def test_rejection_requires_a_reason_and_keeps_account_inactive(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("teacherapproval-reject", args=[self.approval.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(reverse("teacherapproval-reject", args=[self.approval.id]), {
            "notes": "Employment could not be confirmed.",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.approval.refresh_from_db()
        self.teacher_user.refresh_from_db()
        self.assertEqual(self.approval.status, "REJECTED")
        self.assertFalse(self.teacher_user.is_active)

    def test_other_school_admin_cannot_approve(self):
        self.client.force_authenticate(user=self.other_admin)
        response = self.client.post(
            reverse("teacherapproval-approve", args=[self.approval.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, "PENDING")

    def test_set_active_cannot_bypass_the_approval_queue(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/auth/users/{self.teacher_user.id}/set_active/", {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.teacher_user.refresh_from_db()
        self.assertFalse(self.teacher_user.is_active)
