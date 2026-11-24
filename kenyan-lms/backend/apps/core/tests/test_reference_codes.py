"""Tests for automatic business reference numbers."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.content.models import Chapter, DigitalTextbook, Publisher
from apps.core.constants import Roles
from apps.courses.models import Course
from apps.curriculum.models import CurriculumFramework
from apps.institutions.models import Institution, InstitutionType, Subject
from apps.learners.models import Learner
from apps.teachers.models import Teacher

UserModel = get_user_model()


class ReferenceCodeTests(APITestCase):
    def setUp(self):
        self.kind = InstitutionType.objects.create(name="Basic Education")
        self.school = Institution.objects.create(
            name="Kisumu Secondary School", institution_type=self.kind
        )
        self.admin = UserModel.objects.create_user(
            username="code_admin", password="StrongPass123!",
            role=Roles.SCHOOL_ADMIN, institution=self.school,
        )

    def _user(self, username, role=Roles.LEARNER):
        return UserModel.objects.create_user(
            username=username, password="StrongPass123!", role=role, institution=self.school
        )

    def test_institution_type_and_school_codes_are_generated(self):
        self.assertEqual(self.kind.code, "TYP-001")
        self.assertEqual(self.school.code, "KSCH")

        second = Institution.objects.create(name="Kisumu Academy", institution_type=self.kind)
        self.assertEqual(second.code, "KACA")

        duplicate = Institution.objects.create(
            name="Another Kisumu Secondary School", institution_type=self.kind
        )
        self.assertEqual(duplicate.code, "AKSCH")

    def test_admission_and_staff_numbers_increment_per_school(self):
        first = Learner.objects.create(
            user=self._user("learner_a"), institution=self.school
        )
        second = Learner.objects.create(
            user=self._user("learner_b"), institution=self.school
        )
        self.assertEqual(first.admission_number, "ADM-KSCH-001")
        self.assertEqual(second.admission_number, "ADM-KSCH-002")
        self.assertEqual(first.assessment_number, "ASM-KSCH-001")
        self.assertEqual(second.assessment_number, "ASM-KSCH-002")

        teacher = Teacher.objects.create(user=self._user("teacher_a", Roles.TEACHER), institution=self.school)
        teacher2 = Teacher.objects.create(user=self._user("teacher_b", Roles.TEACHER), institution=self.school)
        self.assertEqual(teacher.staff_number, "TCH-KSCH-001")
        self.assertEqual(teacher2.staff_number, "TCH-KSCH-002")

    def test_sequence_is_independent_per_institution(self):
        other = Institution.objects.create(name="Nairobi Academy", institution_type=self.kind)
        learner = Learner.objects.create(user=self._user("learner_c"), institution=other)
        self.assertEqual(learner.admission_number, "ADM-NACA-001")

    def test_course_subject_and_framework_codes_are_generated(self):
        subject = Subject.objects.create(name="Mathematics", institution=self.school)
        course = Course.objects.create(title="Grade 4 Maths", institution=self.school)
        framework = CurriculumFramework.objects.create(name="KICD CBC")
        self.assertEqual(subject.code, "SUB-KSCH-001")
        self.assertEqual(course.code, "CRS-KSCH-001")
        self.assertEqual(framework.code, "CFW-0001")

    def test_publisher_textbook_and_chapter_references(self):
        publisher = Publisher.objects.create(name="KLB")
        textbook = DigitalTextbook.objects.create(title="Mathematics 4", publisher=publisher)
        chapter1 = Chapter.objects.create(textbook=textbook, title="Numbers")
        chapter2 = Chapter.objects.create(textbook=textbook, title="Addition", chapter_number=1)
        self.assertEqual(publisher.code, "PUB-0001")
        self.assertEqual(textbook.isbn, "TB-000001")
        self.assertEqual(chapter1.chapter_number, 1)
        self.assertEqual(chapter2.chapter_number, 2)

    def test_api_creates_learner_without_supplied_admission_number(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("learner-list"), {
            "username": "auto_learner", "first_name": "Ada", "last_name": "Ochieng",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        learner = Learner.objects.get(user__username="auto_learner")
        self.assertEqual(learner.admission_number, "ADM-KSCH-001")
        self.assertEqual(response.data["admission_number"], "ADM-KSCH-001")
