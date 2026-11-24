"""Course isolation and progress tests."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.constants import Roles
from apps.courses.models import Course, Lesson, LessonProgress, Module
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner

User = get_user_model()


class CourseTests(APITestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Primary", code="PRI")
        self.school = Institution.objects.create(name="A", code="A1", institution_type=kind)
        self.other = Institution.objects.create(name="B", code="B1", institution_type=kind)
        self.admin = User.objects.create_user(username="a", password="StrongPass123!", role=Roles.SCHOOL_ADMIN, institution=self.school)
        self.other_admin = User.objects.create_user(username="b", password="StrongPass123!", role=Roles.SCHOOL_ADMIN, institution=self.other)
        self.course = Course.objects.create(institution=self.school, title="Maths", status="PUBLISHED")

    def test_other_school_cannot_see_course(self):
        self.client.force_authenticate(user=self.other_admin)
        response = self.client.get(reverse("course-list"))
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 0)

    def test_other_school_cannot_read_course_detail(self):
        self.client.force_authenticate(user=self.other_admin)
        response = self.client.get(reverse("course-detail", args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_complete_is_idempotent(self):
        learner_user = User.objects.create_user(username="l", password="StrongPass123!", role=Roles.LEARNER, institution=self.school)
        learner = Learner.objects.create(user=learner_user, institution=self.school, admission_number="L1")
        module = Module.objects.create(institution=self.school, course=self.course, title="M1")
        lesson = Lesson.objects.create(institution=self.school, module=module, title="L1")
        self.client.force_authenticate(user=self.admin)
        payload = {"lesson": lesson.id, "learner": learner.id}
        r1 = self.client.post("/api/courses/progress/mark-complete/", payload)
        r2 = self.client.post("/api/courses/progress/mark-complete/", payload)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(LessonProgress.objects.filter(learner=learner, lesson=lesson).count(), 1)

    def test_cannot_create_module_in_another_institution(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/courses/modules/", {
            "course": self.course.id, "title": "Smuggled", "sequence": 1,
            "institution": self.other.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created = Module.objects.get(id=response.data["id"])
        self.assertEqual(created.institution_id, self.school.id)

    def test_cannot_move_course_to_another_institution(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("course-detail", args=[self.course.id]),
            {"institution": self.other.id}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.course.refresh_from_db()
        self.assertEqual(self.course.institution_id, self.school.id)
