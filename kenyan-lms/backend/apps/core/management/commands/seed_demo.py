"""Create a small, realistic demo dataset for exploration.

Run from backend/:  python manage.py seed_demo
Safe to run once. If the demo institution already exists it does nothing.
This only ADDS data; it never deletes or resets anything.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academics.models import SchoolEvent
from apps.assessments.models import Exam, ExamResult, Question, Quiz, QuizQuestion
from apps.attendance.models import AttendanceRecord
from apps.communications.models import Announcement
from apps.content.models import Chapter, ContentAccess, DigitalTextbook, Exercise, Publisher
from apps.core.constants import Roles
from apps.courses.models import Assignment, Course, Lesson, Module
from apps.curriculum.models import (
    Competency, CurriculumFramework, EducationLevel, LearningArea,
    LearningOutcome, Rubric, RubricLevel, Strand, SubStrand,
)
from apps.guardians.models import Guardian
from apps.institutions.models import AcademicYear, Institution, InstitutionType, SchoolClass, Subject, Term
from apps.learners.models import Learner, LearnerGuardian
from apps.teachers.models import Teacher, TeacherClassAssignment

User = get_user_model()
DEMO_CODE = "DEMO01"


class Command(BaseCommand):
    help = "Create demo institution, users and learning data (adds only)."

    def handle(self, *args, **options):
        if Institution.objects.filter(code=DEMO_CODE).exists():
            self.stdout.write("Demo data already present. Nothing changed.")
            return

        primary, _ = InstitutionType.objects.get_or_create(code="PRI", defaults={"name": "Primary School"})
        secondary, _ = InstitutionType.objects.get_or_create(code="SEC", defaults={"name": "Senior School"})

        school = Institution.objects.create(
            name="Mwangaza Demo School", code=DEMO_CODE, institution_type=primary,
            county="Nairobi", town="Nairobi", email="office@mwangaza.demo",
        )

        def make_user(username, role, first, last):
            # No password is stored or printed here. Set one locally with
            # `python manage.py changepassword <username>`.
            return User.objects.create_user(
                username=username, password=None, role=role,
                first_name=first, last_name=last, institution=school,
            )

        admin = make_user("demo_admin", Roles.ADMIN, "Asha", "Mwangi")
        teacher_user = make_user("demo_teacher", Roles.TEACHER, "Joseph", "Kamau")
        guardian_user = make_user("demo_guardian", Roles.GUARDIAN, "Grace", "Otieno")
        learner_user = make_user("demo_learner", Roles.LEARNER, "Amina", "Otieno")

        # Platform superuser (no institution) for exploring platform features.
        if not User.objects.filter(username="platform_admin").exists():
            User.objects.create_user(
                username="platform_admin", password=None,
                role=Roles.SUPER_ADMIN, first_name="Platform", last_name="Admin",
                is_staff=True, is_superuser=True,
            )

        year = AcademicYear.objects.create(
            institution=school, name="2026", start_date=date(2026, 1, 5),
            end_date=date(2026, 11, 27), is_current=True,
        )
        term = Term.objects.create(
            institution=school, academic_year=year, name="Term 1", sequence=1,
            start_date=date(2026, 1, 5), end_date=date(2026, 4, 3), is_current=True,
        )

        maths = Subject.objects.create(institution=school, name="Mathematics", code="MAT", learning_area="Mathematics")
        english = Subject.objects.create(institution=school, name="English", code="ENG", learning_area="Languages")

        grade4 = SchoolClass.objects.create(
            institution=school, academic_year=year, name="Grade 4", level="PRIMARY", stream="A",
        )

        teacher = Teacher.objects.create(user=teacher_user, institution=school, staff_number="T001")
        teacher.subjects.add(maths, english)
        TeacherClassAssignment.objects.create(
            teacher=teacher, institution=school, school_class=grade4, subject=maths,
            academic_year=year, term=term, is_class_teacher=True,
        )

        learner = Learner.objects.create(
            user=learner_user, institution=school, admission_number="ADM001",
            class_room=grade4, date_of_birth=date(2016, 5, 12), gender="F",
            date_admitted=date(2026, 1, 5),
        )
        guardian = Guardian.objects.create(user=guardian_user, institution=school, phone="+254700000000")
        LearnerGuardian.objects.create(learner=learner, guardian=guardian, relationship="Mother", is_primary=True)

        # Attendance for the last five school days.
        today = timezone.now().date()
        for i in range(5):
            AttendanceRecord.objects.create(
                institution=school, learner=learner, school_class=grade4, term=term,
                date=today - timedelta(days=i),
                status="PRESENT" if i != 2 else "LATE", marked_by=teacher_user,
            )

        # Curriculum structure (illustrative, configurable - not hardcoded policy).
        framework = CurriculumFramework.objects.create(
            name="KICD Competency Based Curriculum", code="CBC", version="2017",
            description="Illustrative framework for demonstration.",
        )
        level = EducationLevel.objects.create(framework=framework, name="Primary", code="PRI", sequence=1)
        area = LearningArea.objects.create(level=level, name="Mathematics", code="MAT")
        strand = Strand.objects.create(learning_area=area, name="Numbers", code="NUM")
        sub = SubStrand.objects.create(strand=strand, name="Whole numbers", code="WN")
        outcome = LearningOutcome.objects.create(
            sub_strand=sub, code="MAT.4.1.1",
            description="Represent and compare whole numbers up to 10,000.",
        )
        Competency.objects.create(framework=framework, name="Critical thinking", code="CT")
        rubric = Rubric.objects.create(name="CBE achievement scale")
        for i, (name, lo, hi) in enumerate([
            ("Beginning", 0, 39), ("Developing", 40, 59),
            ("Achieving", 60, 79), ("Extending", 80, 100),
        ], start=1):
            RubricLevel.objects.create(rubric=rubric, name=name, min_score=lo, max_score=hi, sequence=i)

        # Course with a module and lesson.
        course = Course.objects.create(
            institution=school, title="Grade 4 Mathematics", code="G4MAT",
            subject=maths, teacher=teacher, academic_year=year, term=term,
            education_level=level, status="PUBLISHED",
            description="Numbers, operations and problem solving.",
        )
        module = Module.objects.create(institution=school, course=course, title="Whole numbers", sequence=1)
        Lesson.objects.create(
            institution=school, module=module, title="Place value up to 10,000",
            content="Read, write and compare numbers using place value.",
            learning_outcome=outcome, estimated_minutes=20, sequence=1, is_downloadable=True,
        )
        Assignment.objects.create(
            institution=school, course=course, title="Place value practice",
            instructions="Complete exercises 1-5 on place value.",
            max_score=Decimal("20"), created_by=teacher_user, is_published=True,
        )

        # Quiz with auto-marked questions.
        quiz = Quiz.objects.create(institution=school, title="Numbers check", subject=maths, course=course, is_published=True)
        q1 = Question.objects.create(
            institution=school, subject=maths, question_type="MCQ",
            text="What is the value of 7 in 4,738?", options=["7", "70", "700", "7000"],
            correct_answer="700", marks=Decimal("1"), created_by=teacher_user,
        )
        q2 = Question.objects.create(
            institution=school, subject=maths, question_type="TRUE_FALSE",
            text="5,000 is greater than 4,999.", correct_answer="true", marks=Decimal("1"),
            created_by=teacher_user,
        )
        QuizQuestion.objects.create(quiz=quiz, question=q1, sequence=1, marks=Decimal("1"))
        QuizQuestion.objects.create(quiz=quiz, question=q2, sequence=2, marks=Decimal("1"))

        # Exam and a result.
        exam = Exam.objects.create(
            institution=school, title="Term 1 Mathematics", subject=maths,
            school_class=grade4, term=term, academic_year=year,
            exam_date=date(2026, 3, 20), max_score=Decimal("100"),
        )
        ExamResult.objects.create(
            institution=school, exam=exam, learner=learner,
            score=Decimal("78"), grade="B", recorded_by=teacher_user,
        )

        # Digital textbook with a chapter and exercise.
        publisher = Publisher.objects.create(name="KLB Demo Press", code="KLBDEMO")
        book = DigitalTextbook.objects.create(
            publisher=publisher, title="Primary Mathematics Grade 4",
            isbn="978-000-000-000-0", subject=maths, education_level=level,
            curriculum_framework=framework, status="PUBLISHED",
            description="Demonstration textbook.", published_at=timezone.now(),
            license_type="INSTITUTION",
        )
        chapter = Chapter.objects.create(
            textbook=book, title="Whole numbers", chapter_number=1,
            content="Understanding place value.", learning_outcome=outcome, sequence=1,
        )
        Exercise.objects.create(
            chapter=chapter, title="Place value exercises",
            instructions="Answer the questions.",
            questions=[
                {"id": 1, "text": "Value of 7 in 4,738?", "options": ["7", "70", "700", "7000"], "answer": "700"},
            ],
            max_score=Decimal("10"),
        )
        ContentAccess.objects.create(institution=school, textbook=book, is_active=True)

        Announcement.objects.create(
            institution=school, title="Welcome to the new term",
            body="Classes begin on Monday. Please check your timetable.",
            published_by=admin, published_at=timezone.now(), is_published=True, pinned=True,
        )
        SchoolEvent.objects.create(
            institution=school, title="Parents meeting", event_type="MEETING",
            start_datetime=timezone.now() + timedelta(days=7), is_published=True,
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write("Demo usernames:")
        self.stdout.write("  demo_admin     - school administrator")
        self.stdout.write("  demo_teacher   - teacher")
        self.stdout.write("  demo_learner   - learner")
        self.stdout.write("  demo_guardian  - guardian")
        self.stdout.write("  platform_admin - platform superuser")
        self.stdout.write(
            "Passwords are not set or printed. Set one locally with: "
            "python manage.py changepassword <username>"
        )
