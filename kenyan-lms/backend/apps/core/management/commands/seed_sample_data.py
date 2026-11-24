"""Add clearly labelled sample records for demonstration and testing.

Run from backend/:  python manage.py seed_sample_data

The command is additive and safe to re-run. It never deletes or resets data.
All generated records use SMP- references, sample_ usernames and .invalid
email addresses so fictional records are never mistaken for real ones.
"""
from collections import Counter
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from apps.analytics.models import AnalyticsSnapshot, RemediationRule, RemediationTask
from apps.approval.models import ApprovalChecklistItem, ApprovalDecision, ApprovalRequest
from apps.fees.models import FeeInvoice, FeeStructure, Payment
from apps.kemis.models import KemisExport, KemisFieldMapping
from apps.academics.models import SchoolEvent, TimetableEntry
from apps.assessments.models import Answer, Exam, ExamResult, Question, Quiz, QuizAttempt, QuizQuestion
from apps.attendance.models import AttendanceRecord
from apps.communications.models import Announcement, Message, Notification, NotificationPreference
from apps.content.models import Chapter, ContentAccess, ContentResource, DigitalTextbook, Exercise, ExerciseAttempt, Publisher
from apps.core.constants import ContentStatus, Roles
from apps.core.models import AuditLog
from apps.curriculum.models import (
    Competency, CompetencyEvidence, CurriculumFramework, EducationLevel,
    LearningArea, LearningOutcome, Rubric, RubricLevel, Strand, SubStrand,
)
from apps.courses.models import Assignment, Course, Lesson, LessonProgress, Module, Submission
from apps.guardians.models import Guardian
from apps.institutions.models import (
    AcademicYear, Department, Institution, InstitutionType, SchoolClass, Subject, Term,
)
from apps.learners.models import Learner, LearnerGuardian, TransferRecord
from apps.reports.models import ReportSnapshot
from apps.teachers.models import LessonPlan, Teacher, TeacherClassAssignment
from apps.tutor.models import TutorConversation, TutorMessage

User = get_user_model()

TEACHER_NAMES = [
    ("Wanjiku", "Njoroge"), ("Otieno", "Okoth"), ("Achieng", "Owino"),
    ("Muthoni", "Kamau"), ("Kiprop", "Chebet"), ("Njeri", "Mwangi"),
    ("Omondi", "Odhiambo"), ("Wairimu", "Kariuki"), ("Kipchoge", "Rono"),
    ("Akinyi", "Ouma"), ("Mwangi", "Waititu"), ("Chepkemoi", "Kiptoo"),
]
LEARNER_NAMES = [
    ("Amina", "Hassan"), ("Brian", "Kiptoo"), ("Cynthia", "Wambui"),
    ("David", "Omondi"), ("Esther", "Njoroge"), ("Felix", "Mwangi"),
    ("Grace", "Akinyi"), ("Hussein", "Ali"), ("Ivy", "Chebet"),
    ("Jonathan", "Otieno"), ("Kevin", "Muthomi"), ("Lydia", "Wanjiku"),
]
GUARDIAN_NAMES = [
    ("Mary", "Wambui"), ("Samuel", "Omondi"), ("Jane", "Akinyi"),
    ("Peter", "Kiptoo"), ("Grace", "Njeri"), ("Daniel", "Otieno"),
    ("Anne", "Muthoni"), ("Francis", "Mwangi"), ("Rebecca", "Chebet"),
    ("Joseph", "Ali"), ("Catherine", "Wanjiku"), ("Zachary", "Kiprop"),
]
SUBJECT_NAMES = [
    "Mathematics", "English", "Kiswahili", "Integrated Science",
    "Social Studies", "Religious Education", "Creative Arts",
    "Physical and Health Education", "Agriculture", "Home Science",
    "Computing", "French",
]
DEPARTMENT_NAMES = [
    "Mathematics", "Languages", "Science", "Humanities", "Creative Arts",
    "Physical Education", "Guidance and Counselling", "ICT", "Agriculture",
    "Religious Studies", "Special Needs", "Library Services",
]
AREA_NAMES = [
    "Language and Communication", "Mathematics", "Science and Technology",
    "Social and Environmental Studies", "Religious and Moral Education",
    "Creative and Performing Arts", "Physical and Health Education",
    "Agriculture and Nutrition", "Computing and Digital Literacy",
    "Life Skills", "Kiswahili Studies", "English Studies",
]
COMPETENCY_NAMES = [
    "Critical thinking", "Creative problem solving", "Communication",
    "Collaboration", "Digital literacy", "Self-efficacy",
    "Citizenship", "Cultural awareness", "Leadership",
    "Research skills", "Financial literacy", "Environmental stewardship",
]
SAMPLE_TYPES = [
    ("Sample Primary School", "SMP-T01", "Sample primary-level institution."),
    ("Sample Senior School", "SMP-T02", "Sample senior-level institution."),
    ("Sample Early Childhood Centre", "SMP-T03", "Sample pre-primary institution."),
    ("Sample Technical Institute", "SMP-T04", "Sample TVET institution."),
    ("Sample Special School", "SMP-T05", "Sample special-needs institution."),
    ("Sample Alternative School", "SMP-T06", "Sample alternative learning institution."),
    ("Sample Community School", "SMP-T07", "Sample community-run institution."),
    ("Sample Boarding School", "SMP-T08", "Sample residential institution."),
    ("Sample Adult Education Centre", "SMP-T09", "Sample adult learning institution."),
    ("Sample Online Academy", "SMP-T10", "Sample distance-learning institution."),
]
COUNTIES = [
    "Nairobi", "Kiambu", "Kisumu", "Mombasa", "Nakuru", "Machakos",
    "Uasin Gishu", "Kakamega", "Meru", "Bungoma",
]
GRADE_LEVELS = ["Grade 4", "Grade 5", "Grade 6"]
STREAMS = ["A", "B", "C", "D"]
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
ATTENDANCE_PATTERN = [
    "PRESENT", "PRESENT", "PRESENT", "PRESENT", "PRESENT",
    "PRESENT", "LATE", "PRESENT", "ABSENT", "PRESENT", "EXCUSED",
]
TRACKED_MODELS = [
    "accounts.User", "institutions.InstitutionType", "institutions.Institution",
    "institutions.AcademicYear", "institutions.Term", "institutions.SchoolClass",
    "institutions.Subject", "institutions.Department", "learners.Learner", "learners.LearnerGuardian",
    "learners.TransferRecord", "teachers.Teacher", "teachers.TeacherClassAssignment",
    "teachers.LessonPlan", "guardians.Guardian", "academics.TimetableEntry",
    "academics.SchoolEvent", "attendance.AttendanceRecord",
    "curriculum.CurriculumFramework", "curriculum.EducationLevel",
    "curriculum.LearningArea", "curriculum.Strand", "curriculum.SubStrand",
    "curriculum.LearningOutcome", "curriculum.Competency", "curriculum.Rubric",
    "curriculum.RubricLevel", "curriculum.CompetencyEvidence",
    "courses.Course", "courses.Module", "courses.Lesson", "courses.LessonProgress",
    "courses.Assignment", "courses.Submission", "assessments.Question",
    "assessments.Quiz", "assessments.QuizQuestion", "assessments.QuizAttempt",
    "assessments.Answer", "assessments.Exam", "assessments.ExamResult",
    "content.Publisher", "content.DigitalTextbook", "content.Chapter",
    "content.ContentResource", "content.Exercise", "content.ExerciseAttempt",
    "content.ContentAccess", "communications.Announcement",
    "communications.Notification", "communications.Message",
    "communications.NotificationPreference", "reports.ReportSnapshot", "core.AuditLog",
    "fees.FeeStructure", "fees.FeeInvoice", "fees.Payment",
    "approval.ApprovalRequest", "approval.ApprovalDecision", "approval.ApprovalChecklistItem",
    "kemis.KemisExport", "kemis.KemisFieldMapping",
    "tutor.TutorConversation", "tutor.TutorMessage",
    "analytics.AnalyticsSnapshot", "analytics.RemediationRule", "analytics.RemediationTask",
]


def grade_for(score):
    score = float(score)
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "E"


def recent_school_days(count):
    days = []
    cursor = timezone.localdate()
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


class Command(BaseCommand):
    help = "Add 10+ labelled sample records per category to the demo institution (adds only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--institution-code",
            default="DEMO01",
            help="Code of the institution to receive sample records (default: DEMO01).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        code = options["institution_code"]
        school = Institution.objects.filter(code=code).first()
        if school is None:
            raise CommandError(
                f"Institution {code!r} does not exist. Run `python manage.py seed_demo` first."
            )

        self.school = school
        self.created = Counter()

        types = self.seed_institutions()
        years, current_year = self.seed_calendar()
        terms = self.seed_terms(years)
        classes = self.seed_classes(current_year)
        subjects = self.seed_subjects()
        self.seed_departments()
        teachers = self.seed_teachers(subjects)
        learners = self.seed_learners(classes)
        guardians = self.seed_guardians(learners)
        self.seed_teacher_assignments(teachers, classes, subjects, current_year, terms)
        self.seed_lesson_plans(teachers, classes, subjects)
        self.seed_timetable(classes, terms[0], subjects, teachers)

        framework, levels, outcomes, competencies, rubric_levels = self.seed_curriculum()
        courses, modules, lessons = self.seed_courses(
            subjects, teachers, current_year, terms[0], levels, outcomes
        )
        self.seed_lesson_progress(learners, lessons)
        assignments = self.seed_assignments(courses, lessons, teachers)
        self.seed_submissions(assignments, learners, teachers)
        questions, quizzes, quiz_questions = self.seed_assessments(
            subjects, courses, outcomes, teachers
        )
        self.seed_quiz_attempts(quizzes, quiz_questions, learners)
        exams = self.seed_exams(subjects, classes, terms, current_year)
        self.seed_exam_results(exams, learners, teachers)

        textbooks, chapters, exercises = self.seed_content(
            subjects, framework, outcomes
        )
        self.seed_content_activity(exercises, learners, textbooks)

        # Extended modules: fees, internal review, local exports, tutor and
        # analytics. All records stay inside the labelled demo institution.
        self.seed_fees(learners, terms, classes, teachers)
        self.seed_approval(textbooks, teachers)
        self.seed_kemis(teachers)
        self.seed_tutor(learners, teachers)
        self.seed_analytics_records(competencies, learners, teachers)

        self.seed_communications(teachers, learners, guardians, outcomes, competencies, rubric_levels)
        self.seed_transfer_records(learners, types)
        self.seed_snapshots(teachers)
        self.seed_audit_log(teachers)

        self.report()

    def ensure(self, model, category, lookup, **defaults):
        obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
        if created:
            self.created[category] += 1
        return obj

    def ensure_by(self, model, category, lookup, **defaults):
        """For models without a database unique constraint."""
        obj = model.objects.filter(**lookup).first()
        if obj:
            return obj
        values = dict(defaults)
        values.update(lookup)
        obj = model.objects.create(**values)
        self.created[category] += 1
        return obj

    def make_user(self, username, role, first, last, institution=None):
        user = User.objects.filter(username=username).first()
        if user:
            return user
        user = User.objects.create_user(
            username=username,
            email=f"{username}@sample.invalid",
            first_name=first,
            last_name=last,
            role=role,
            institution=institution,
            password=None,  # Never store or print a password.
        )
        self.created["accounts.User"] += 1
        return user

    def seed_institutions(self):
        labels = []
        for name, code, description in SAMPLE_TYPES:
            item = self.ensure(
                InstitutionType, "institutions.InstitutionType",
                {"name": name}, code=code, description=description,
            )
            labels.append(item)

        for index, county in enumerate(COUNTIES[:9], start=1):
            code = f"SMP{index:02d}"
            self.ensure(
                Institution, "institutions.Institution",
                {"code": code},
                name=f"Sample County Academy {index:02d}",
                institution_type=labels[index % len(labels)],
                county=county,
                town=county,
                email=f"office{index:02d}@sample.invalid",
                phone=f"+2547{10000000 + index:08d}",
                motto="Learning grounded in community",
                address_line=f"Sample Street {index}, {county}",
                settings={"sample_data": True, "seeded_by": "seed_sample_data"},
            )
        return labels

    def seed_calendar(self):
        current = None
        years = []
        for year in range(2017, 2027):
            item = self.ensure(
                AcademicYear, "institutions.AcademicYear",
                {"institution": self.school, "name": str(year)},
                start_date=date(year, 1, 5),
                end_date=date(year, 11, 27),
                is_current=year == 2026,
            )
            years.append(item)
            if year == 2026:
                current = item
        return years, current

    def seed_terms(self, years):
        ranges = [
            ("Term 1", 1, (1, 5), (4, 3)),
            ("Term 2", 2, (4, 20), (7, 24)),
            ("Term 3", 3, (9, 7), (11, 27)),
        ]
        terms = []
        for year in years:
            year_number = int(year.name)
            for name, sequence, start, end in ranges:
                item = self.ensure(
                    Term, "institutions.Term",
                    {"academic_year": year, "name": name},
                    institution=self.school,
                    start_date=date(year_number, *start),
                    end_date=date(year_number, *end),
                    sequence=sequence,
                    is_current=year_number == 2026 and name == "Term 1",
                )
                terms.append(item)
        return terms

    def seed_classes(self, current_year):
        classes = []
        for grade in GRADE_LEVELS:
            for stream in STREAMS:
                item = self.ensure(
                    SchoolClass, "institutions.SchoolClass",
                    {
                        "institution": self.school,
                        "academic_year": current_year,
                        "name": grade,
                        "stream": stream,
                    },
                    level="PRIMARY",
                    capacity=40,
                )
                classes.append(item)
        return classes

    def seed_subjects(self):
        subjects = []
        for index, name in enumerate(SUBJECT_NAMES, start=1):
            item = self.ensure(
                Subject, "institutions.Subject",
                {"institution": self.school, "name": name},
                learning_area=AREA_NAMES[(index - 1) % len(AREA_NAMES)],
                is_active=True,
            )
            subjects.append(item)
        return subjects

    def seed_departments(self):
        for index, name in enumerate(DEPARTMENT_NAMES, start=1):
            self.ensure(
                Department, "institutions.Department",
                {"institution": self.school, "name": name},
                description=f"Sample organisational unit {index:02d}.",
                head_of_department=TEACHER_NAMES[index % len(TEACHER_NAMES)][0] + " " + TEACHER_NAMES[index % len(TEACHER_NAMES)][1],
                is_active=index < len(DEPARTMENT_NAMES),
            )

    def seed_teachers(self, subjects):
        teachers = []
        for index, (first, last) in enumerate(TEACHER_NAMES, start=1):
            username = f"sample_teacher_{index:02d}"
            user = self.make_user(username, Roles.TEACHER, first, last, self.school)
            teacher = self.ensure(
                Teacher, "teachers.Teacher", {"user": user},
                institution=self.school,
                employment_type=["PERMANENT", "CONTRACT", "PART_TIME"][index % 3],
                phone=f"+2547{20000000 + index:08d}",
                is_active=True,
            )
            teacher.subjects.set([subjects[(index - 1) % 12], subjects[(index + 2) % 12]])
            teachers.append(teacher)
        return teachers

    def seed_learners(self, classes):
        learners = []
        for index, (first, last) in enumerate(LEARNER_NAMES, start=1):
            username = f"sample_learner_{index:02d}"
            user = self.make_user(username, Roles.LEARNER, first, last, self.school)
            status = "ACTIVE" if index <= 10 else (["SUSPENDED", "ALUMNI"][index - 11])
            learner = self.ensure(
                Learner, "learners.Learner",
                {"institution": self.school, "admission_number": f"SMP-ADM-{index:03d}"},
                user=user,
                assessment_number=f"SMP-ASM-{index:03d}",
                date_of_birth=date(2014 + (index % 4), 1 + (index % 12), 5 + (index % 20)),
                gender="F" if index % 2 else "M",
                class_room=classes[(index - 1) % len(classes)],
                status=status,
                date_admitted=date(2026, 1, 5 + (index % 10)),
                date_left=date(2026, 6, 30) if status == "ALUMNI" else None,
                previous_school="Sample Community School" if index % 3 == 0 else "",
            )
            learners.append(learner)
        return learners

    def seed_guardians(self, learners):
        guardians = []
        for index, (first, last) in enumerate(GUARDIAN_NAMES, start=1):
            username = f"sample_guardian_{index:02d}"
            user = self.make_user(username, Roles.GUARDIAN, first, last, self.school)
            guardian = self.ensure(
                Guardian, "guardians.Guardian", {"user": user},
                institution=self.school,
                phone=f"+2547{30000000 + index:08d}",
                occupation=["Teacher", "Trader", "Nurse", "Farmer", "Engineer"][index % 5],
                relationship_to_learner="Parent",
                preferred_language="en",
                receive_sms=index % 2 == 0,
            )
            self.ensure(
                LearnerGuardian, "learners.LearnerGuardian",
                {"learner": learners[index - 1], "guardian": guardian},
                relationship="Mother" if index % 2 else "Father",
                is_primary=True,
                can_view_academics=True,
                can_view_attendance=True,
                can_view_fees=index % 3 == 0,
            )
            if index <= 2:
                self.ensure(
                    LearnerGuardian, "learners.LearnerGuardian",
                    {"learner": learners[index + 9], "guardian": guardian},
                    relationship="Guardian",
                    is_primary=False,
                    can_view_academics=True,
                    can_view_attendance=True,
                    can_view_fees=False,
                )
            self.ensure(
                NotificationPreference, "communications.NotificationPreference",
                {"user": user},
                in_app=True,
                email=index % 2 == 0,
                sms=False,
                types=["ACADEMIC", "ATTENDANCE"],
            )
            guardians.append(guardian)
        return guardians

    def seed_teacher_assignments(self, teachers, classes, subjects, year, terms):
        for index, teacher in enumerate(teachers):
            school_class = classes[index % len(classes)]
            subject = subjects[index % len(subjects)]
            self.ensure(
                TeacherClassAssignment, "teachers.TeacherClassAssignment",
                {
                    "teacher": teacher, "school_class": school_class,
                    "subject": subject, "academic_year": year,
                },
                institution=self.school,
                term=terms[0],
                is_class_teacher=index < len(classes),
            )

    def seed_lesson_plans(self, teachers, classes, subjects):
        for index, teacher in enumerate(teachers):
            self.ensure_by(
                LessonPlan, "teachers.LessonPlan",
                {
                    "teacher": teacher, "school_class": classes[index % len(classes)],
                    "subject": subjects[index % len(subjects)],
                    "title": f"Sample lesson plan {index + 1:02d}",
                },
                institution=self.school,
                school_class=classes[index % len(classes)],
                subject=subjects[index % len(subjects)],
                title=f"Sample lesson plan {index + 1:02d}",
                objectives=f"Learners will describe sample concept {index + 1}.",
                content="Illustrative content for testing lesson plans.",
                planned_date=timezone.localdate() + timedelta(days=index),
                status=["DRAFT", "SUBMITTED", "APPROVED"][index % 3],
            )

    def seed_timetable(self, classes, term, subjects, teachers):
        times = [("08:00", "08:40"), ("08:40", "09:20"), ("09:40", "10:20")]
        for index in range(12):
            start, end = times[index % len(times)]
            self.ensure_by(
                TimetableEntry, "academics.TimetableEntry",
                {
                    "school_class": classes[index % len(classes)],
                    "term": term,
                    "subject": subjects[index % len(subjects)],
                    "day_of_week": WEEKDAYS[index % len(WEEKDAYS)],
                    "start_time": start,
                },
                institution=self.school,
                school_class=classes[index % len(classes)],
                term=term,
                subject=subjects[index % len(subjects)],
                teacher=teachers[index % len(teachers)],
                day_of_week=WEEKDAYS[index % len(WEEKDAYS)],
                start_time=start,
                end_time=end,
            )

    def seed_curriculum(self):
        frameworks = []
        for index in range(1, 10):
            frameworks.append(self.ensure(
                CurriculumFramework, "curriculum.CurriculumFramework",
                {"name": f"Sample Curriculum Framework {index:02d}", "version": "1.0"},
                code=f"SMP-CFW-{index:02d}",
                description="Fictional framework for testing only.",
                is_active=True,
            ))
        main = CurriculumFramework.objects.filter(name__icontains="KICD").first() or frameworks[0]

        levels = []
        for index in range(1, 13):
            levels.append(self.ensure(
                EducationLevel, "curriculum.EducationLevel",
                {"framework": main, "code": f"SMP-LVL-{index:02d}"},
                name=f"Sample Level {index:02d}",
                sequence=index,
            ))
        areas = []
        for index, name in enumerate(AREA_NAMES, start=1):
            areas.append(self.ensure(
                LearningArea, "curriculum.LearningArea",
                {"level": levels[0], "name": name},
                code=f"SMP-LA-{index:02d}",
                sequence=index,
            ))
        strands = []
        for index in range(1, 13):
            strands.append(self.ensure(
                Strand, "curriculum.Strand",
                {"learning_area": areas[0], "name": f"Sample Strand {index:02d}"},
                code=f"SMP-STR-{index:02d}",
                sequence=index,
            ))
        substrands = []
        for index in range(1, 13):
            substrands.append(self.ensure(
                SubStrand, "curriculum.SubStrand",
                {"strand": strands[0], "name": f"Sample Sub-strand {index:02d}"},
                code=f"SMP-SS-{index:02d}",
                sequence=index,
                recommended_hours=8 + index,
            ))
        outcomes = []
        for index in range(1, 13):
            outcomes.append(self.ensure(
                LearningOutcome, "curriculum.LearningOutcome",
                {"sub_strand": substrands[0], "code": f"SMP-LO-{index:02d}"},
                description=f"Sample learning outcome {index:02d} for testing reports.",
                sequence=index,
            ))
        competencies = []
        for index, name in enumerate(COMPETENCY_NAMES, start=1):
            competencies.append(self.ensure(
                Competency, "curriculum.Competency",
                {"framework": main, "name": name},
                code=f"SMP-CMP-{index:02d}",
                description="Sample competency used for testing.",
            ))
        rubric_levels = []
        for index in range(1, 10):
            rubric = self.ensure(
                Rubric, "curriculum.Rubric",
                {"name": f"Sample Rubric {index:02d}"},
                institution=self.school,
                description="Illustrative achievement rubric.",
            )
            for level_index, (name, lo, hi) in enumerate([
                ("Beginning", 0, 39), ("Developing", 40, 59),
                ("Achieving", 60, 79), ("Extending", 80, 100),
            ], start=1):
                rubric_levels.append(self.ensure(
                    RubricLevel, "curriculum.RubricLevel",
                    {"rubric": rubric, "name": name},
                    min_score=Decimal(lo), max_score=Decimal(hi), sequence=level_index,
                ))
        return main, levels, outcomes, competencies, rubric_levels

    def seed_courses(self, subjects, teachers, year, term, levels, outcomes):
        courses, modules, lessons = [], [], []
        for index in range(1, 13):
            course = self.ensure_by(
                Course, "courses.Course",
                {"institution": self.school, "title": f"Sample Course {index:02d}"},
                institution=self.school,
                code=f"SMP-CRS-{index:03d}",
                title=f"Sample Course {index:02d}",
                description=f"Sample course {index} for testing learning analytics.",
                subject=subjects[(index - 1) % len(subjects)],
                teacher=teachers[(index - 1) % len(teachers)],
                academic_year=year,
                term=term,
                education_level=levels[(index - 1) % len(levels)],
                status=ContentStatus.PUBLISHED,
            )
            courses.append(course)
            for module_index in range(1, 3):
                module = self.ensure_by(
                    Module, "courses.Module",
                    {"course": course, "title": f"Sample Module {module_index:02d}"},
                    institution=self.school,
                    course=course,
                    title=f"Sample Module {module_index:02d}",
                    description="Illustrative module.",
                    sequence=module_index,
                )
                modules.append(module)
                lesson = self.ensure_by(
                    Lesson, "courses.Lesson",
                    {"module": module, "title": f"Sample Lesson {module_index:02d}"},
                    institution=self.school,
                    module=module,
                    title=f"Sample Lesson {module_index:02d}",
                    content="Sample lesson content for offline and online testing.",
                    content_type="TEXT",
                    learning_outcome=outcomes[(index - 1) % len(outcomes)],
                    estimated_minutes=15 + module_index * 5,
                    sequence=module_index,
                    is_downloadable=True,
                )
                lessons.append(lesson)
        return courses, modules, lessons

    def seed_lesson_progress(self, learners, lessons):
        statuses = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "COMPLETED"]
        for learner_index, learner in enumerate(learners):
            for lesson_index, lesson in enumerate(lessons[:12]):
                status = statuses[(learner_index + lesson_index) % len(statuses)]
                self.ensure(
                    LessonProgress, "courses.LessonProgress",
                    {"learner": learner, "lesson": lesson},
                    institution=self.school,
                    status=status,
                    time_spent_seconds=(lesson_index + 1) * 120 if status != "NOT_STARTED" else 0,
                    completed_at=timezone.now() if status == "COMPLETED" else None,
                )

    def seed_assignments(self, courses, lessons, teachers):
        assignments = []
        for index, course in enumerate(courses, start=1):
            assignment = self.ensure_by(
                Assignment, "courses.Assignment",
                {"course": course, "title": f"Sample Assignment {index:02d}"},
                institution=self.school,
                course=course,
                lesson=lessons[(index - 1) % len(lessons)],
                title=f"Sample Assignment {index:02d}",
                instructions="Answer all sample questions and show your working.",
                due_date=timezone.now() + timedelta(days=7 + index),
                max_score=Decimal("20"),
                created_by=teachers[(index - 1) % len(teachers)].user,
                is_published=True,
            )
            assignments.append(assignment)
        return assignments

    def seed_submissions(self, assignments, learners, teachers):
        for assignment_index, assignment in enumerate(assignments[:6]):
            for learner_index, learner in enumerate(learners):
                status = ["GRADED", "SUBMITTED", "RETURNED"][(assignment_index + learner_index) % 3]
                score = Decimal(12 + ((assignment_index * 5 + learner_index * 3) % 9))
                self.ensure(
                    Submission, "courses.Submission",
                    {"assignment": assignment, "learner": learner},
                    institution=self.school,
                    text_answer="Sample written answer for testing grading flow.",
                    status=status,
                    score=score if status != "SUBMITTED" else None,
                    feedback="Clear reasoning." if status != "SUBMITTED" else "",
                    graded_by=teachers[learner_index % len(teachers)].user if status != "SUBMITTED" else None,
                    graded_at=timezone.now() if status != "SUBMITTED" else None,
                )

    def seed_assessments(self, subjects, courses, outcomes, teachers):
        questions = []
        for index in range(1, 25):
            kind = ["MCQ", "TRUE_FALSE", "SHORT"][index % 3]
            if kind == "MCQ":
                options = ["12", "24", "36", "48"]
                answer = "24"
            elif kind == "TRUE_FALSE":
                options = []
                answer = "true" if index % 2 else "false"
            else:
                options = []
                answer = f"Sample answer {index}"
            questions.append(self.ensure_by(
                Question, "assessments.Question",
                {"institution": self.school, "text": f"Sample question {index:02d}?"},
                institution=self.school,
                subject=subjects[index % len(subjects)],
                learning_outcome=outcomes[index % len(outcomes)],
                question_type=kind,
                text=f"Sample question {index:02d}?",
                options=options,
                correct_answer=answer,
                marks=Decimal("1"),
                explanation="Illustrative question for testing only.",
                created_by=teachers[index % len(teachers)].user,
            ))

        quizzes, quiz_questions = [], []
        for index in range(1, 13):
            quiz = self.ensure_by(
                Quiz, "assessments.Quiz",
                {"institution": self.school, "title": f"Sample Quiz {index:02d}"},
                institution=self.school,
                title=f"Sample Quiz {index:02d}",
                description="Auto-generated sample quiz.",
                course=courses[(index - 1) % len(courses)],
                subject=subjects[(index - 1) % len(subjects)],
                time_limit_minutes=20 + index,
                is_published=True,
            )
            quizzes.append(quiz)
            for question_index in range(2):
                question = questions[(index * 2 + question_index) % len(questions)]
                quiz_questions.append(self.ensure(
                    QuizQuestion, "assessments.QuizQuestion",
                    {"quiz": quiz, "question": question},
                    sequence=question_index + 1,
                    marks=Decimal("1"),
                ))
        return questions, quizzes, quiz_questions

    def seed_quiz_attempts(self, quizzes, quiz_questions, learners):
        for quiz_index, quiz in enumerate(quizzes[:6]):
            questions = [link.question for link in quiz_questions if link.quiz_id == quiz.id][:2]
            for learner_index, learner in enumerate(learners):
                attempt = self.ensure_by(
                    QuizAttempt, "assessments.QuizAttempt",
                    {"quiz": quiz, "learner": learner},
                    institution=self.school,
                    quiz=quiz,
                    learner=learner,
                    score=Decimal(1 + ((quiz_index + learner_index) % 2)),
                    max_score=Decimal("2"),
                    status="COMPLETED",
                    completed_at=timezone.now(),
                    synced_at=timezone.now(),
                )
                for question_index, question in enumerate(questions):
                    correct = question_index == 0 or (quiz_index + learner_index) % 3 == 0
                    self.ensure(
                        Answer, "assessments.Answer",
                        {"attempt": attempt, "question": question},
                        answer_text=question.correct_answer if correct else "Sample incorrect answer",
                        is_correct=correct,
                        marks_obtained=Decimal("1") if correct else Decimal("0"),
                    )

    def seed_exams(self, subjects, classes, terms, year):
        exams = []
        for index in range(1, 13):
            exam = self.ensure_by(
                Exam, "assessments.Exam",
                {
                    "institution": self.school,
                    "title": f"Sample Term 1 Assessment {index:02d}",
                    "exam_date": date(2026, 2, 5 + index),
                },
                institution=self.school,
                title=f"Sample Term 1 Assessment {index:02d}",
                subject=subjects[(index - 1) % len(subjects)],
                school_class=classes[(index - 1) % len(classes)],
                term=terms[0],
                academic_year=year,
                exam_date=date(2026, 2, 5 + index),
                max_score=Decimal("100"),
            )
            exams.append(exam)
        return exams

    def seed_exam_results(self, exams, learners, teachers):
        for exam_index, exam in enumerate(exams):
            rows = []
            for learner_index, learner in enumerate(learners):
                score = Decimal(48 + ((exam_index * 7 + learner_index * 5) % 51))
                result = self.ensure(
                    ExamResult, "assessments.ExamResult",
                    {"exam": exam, "learner": learner},
                    institution=self.school,
                    score=score,
                    grade=grade_for(score),
                    remarks="Sample result for testing analytics.",
                    recorded_by=teachers[exam_index % len(teachers)].user,
                )
                rows.append((score, result))
            for position, (_, result) in enumerate(sorted(rows, key=lambda row: row[0], reverse=True), start=1):
                if result.position != position:
                    result.position = position
                    result.save(update_fields=["position"])

    def seed_content(self, subjects, framework, outcomes):
        publishers, textbooks, chapters, exercises = [], [], [], []
        for index in range(1, 13):
            publisher = self.ensure(
                Publisher, "content.Publisher",
                {"name": f"Sample Publisher {index:02d}"},
                code=f"SMP-PUB-{index:02d}",
                website=f"https://sample{index:02d}.invalid",
            )
            publishers.append(publisher)
            book = self.ensure_by(
                DigitalTextbook, "content.DigitalTextbook",
                {"publisher": publisher, "title": f"Sample Textbook {index:02d}"},
                publisher=publisher,
                title=f"Sample Textbook {index:02d}",
                subtitle="Fictional catalogue title used for testing.",
                isbn=f"SMP-TB-{index:06d}",
                subject=subjects[(index - 1) % len(subjects)],
                education_level=None,
                curriculum_framework=framework,
                description="Sample textbook with licensed access for the demo school.",
                license_type="INSTITUTION",
                status=ContentStatus.PUBLISHED,
                published_at=timezone.now(),
            )
            textbooks.append(book)
            for chapter_index in (1, 2):
                chapter = self.ensure(
                    Chapter, "content.Chapter",
                    {"textbook": book, "chapter_number": chapter_index},
                    title=f"Sample Chapter {chapter_index:02d}",
                    content="Illustrative chapter content.",
                    learning_outcome=outcomes[(index + chapter_index) % len(outcomes)],
                    is_downloadable=True,
                    sequence=chapter_index,
                )
                chapters.append(chapter)
                resource = self.ensure_by(
                    ContentResource, "content.ContentResource",
                    {"chapter": chapter, "title": f"Sample Resource {chapter_index:02d}"},
                    chapter=chapter,
                    textbook=book,
                    title=f"Sample Resource {chapter_index:02d}",
                    resource_type=["PDF", "VIDEO", "AUDIO", "LINK"][chapter_index % 4],
                    external_url=f"https://sample.invalid/resource/{index:02d}-{chapter_index}",
                    description="Sample resource for testing catalogue views.",
                    offline_available=chapter_index == 1,
                    size_kb=120 + index * 10,
                )
                exercise = self.ensure_by(
                    Exercise, "content.Exercise",
                    {"chapter": chapter, "title": f"Sample Exercise {chapter_index:02d}"},
                    chapter=chapter,
                    title=f"Sample Exercise {chapter_index:02d}",
                    instructions="Answer the sample questions.",
                    questions=[
                        {"id": 1, "text": "Sample one?", "options": ["Yes", "No"], "answer": "Yes"},
                        {"id": 2, "text": "Sample two?", "options": ["A", "B"], "answer": "A"},
                    ],
                    max_score=Decimal("10"),
                    sequence=chapter_index,
                )
                exercises.append(exercise)
            self.ensure(
                ContentAccess, "content.ContentAccess",
                {"institution": self.school, "textbook": book},
                is_active=True,
                valid_from=date(2026, 1, 1),
                valid_until=date(2026, 12, 31),
            )
        return textbooks, chapters, exercises

    def seed_content_activity(self, exercises, learners, textbooks):
        for exercise_index, exercise in enumerate(exercises[:6]):
            for learner_index, learner in enumerate(learners):
                self.ensure_by(
                    ExerciseAttempt, "content.ExerciseAttempt",
                    {"exercise": exercise, "learner": learner},
                    institution=self.school,
                    exercise=exercise,
                    learner=learner,
                    answers=[{"id": 1, "answer": "Yes"}, {"id": 2, "answer": "A"}],
                    score=Decimal(6 + ((exercise_index + learner_index) % 5)),
                    completed_at=timezone.now(),
                    synced_at=timezone.now(),
                )
        for index, learner in enumerate(learners):
            self.ensure_by(
                AttendanceRecord, "attendance.AttendanceRecord",
                {
                    "learner": learner,
                    "date": recent_school_days(1)[0],
                },
                institution=self.school,
                learner=learner,
                school_class=learner.class_room,
                term=None,
                date=recent_school_days(1)[0],
                status=ATTENDANCE_PATTERN[index % len(ATTENDANCE_PATTERN)],
                marked_by=User.objects.filter(role=Roles.TEACHER, institution=self.school).first(),
                notes="Sample attendance record.",
            )
        dates = recent_school_days(20)
        for index, learner in enumerate(learners):
            for day_index, day in enumerate(dates):
                status = ATTENDANCE_PATTERN[(index * 3 + day_index) % len(ATTENDANCE_PATTERN)]
                self.ensure(
                    AttendanceRecord, "attendance.AttendanceRecord",
                    {"learner": learner, "date": day},
                    institution=self.school,
                    learner=learner,
                    school_class=learner.class_room,
                    term=None,
                    status=status,
                    marked_by=User.objects.filter(role=Roles.TEACHER, institution=self.school).first(),
                    notes=f"Sample {status.lower()} record." if status != "PRESENT" else "",
                )

    def seed_communications(self, teachers, learners, guardians, outcomes, competencies, rubric_levels):
        publisher = teachers[0].user
        for index in range(1, 13):
            self.ensure_by(
                Announcement, "communications.Announcement",
                {"institution": self.school, "title": f"Sample Announcement {index:02d}"},
                institution=self.school,
                title=f"Sample Announcement {index:02d}",
                body="This is a sample announcement used to test messaging and offline sync.",
                audience_roles=[Roles.LEARNER, Roles.GUARDIAN] if index % 2 else [],
                published_by=publisher,
                published_at=timezone.now(),
                is_published=True,
                pinned=index == 1,
            )
            start_at = timezone.make_aware(
                datetime.combine(date(2026, 12, 1) + timedelta(days=index), time(9, 0))
            )
            self.ensure_by(
                SchoolEvent, "academics.SchoolEvent",
                {
                    "institution": self.school,
                    "title": f"Sample Event {index:02d}",
                },
                institution=self.school,
                title=f"Sample Event {index:02d}",
                description="Illustrative school event.",
                event_type=["MEETING", "EXAM", "SPORTS", "HOLIDAY", "OTHER"][index % 5],
                start_datetime=start_at,
                is_published=True,
            )
            self.ensure(
                CompetencyEvidence, "curriculum.CompetencyEvidence",
                {
                    "learner": learners[index % len(learners)],
                    "evidence_type": "OBSERVATION",
                    "notes": f"Sample evidence {index:02d}",
                },
                institution=self.school,
                learner=learners[index % len(learners)],
                outcome=outcomes[index % len(outcomes)],
                competency=competencies[index % len(competencies)],
                rubric_level=rubric_levels[index % len(rubric_levels)],
                achieved_level=["BEGINNING", "DEVELOPING", "ACHIEVING", "EXTENDING"][index % 4],
                evidence_type="OBSERVATION",
                notes=f"Sample evidence {index:02d}",
                recorded_by=publisher,
            )
            recipient = guardians[(index - 1) % len(guardians)].user
            self.ensure_by(
                Notification, "communications.Notification",
                {"recipient": recipient, "title": f"Sample Notification {index:02d}"},
                recipient=recipient,
                title=f"Sample Notification {index:02d}",
                body="Sample notification for testing the message centre.",
                notification_type=["GENERAL", "ACADEMIC", "ATTENDANCE", "MESSAGE"][index % 4],
                link="/portal/communications",
                is_read=index % 3 == 0,
            )
            sender = teachers[(index - 1) % len(teachers)].user
            target = learners[(index - 1) % len(learners)].user
            self.ensure_by(
                Message, "communications.Message",
                {"sender": sender, "recipient": target, "subject": f"Sample Message {index:02d}"},
                sender=sender,
                recipient=target,
                subject=f"Sample Message {index:02d}",
                body="This sample message tests direct communication between staff and learners.",
                is_read=index % 4 == 0,
            )

    def seed_transfer_records(self, learners, types):
        destination = Institution.objects.filter(code="SMP01").first()
        for index in range(1, 11):
            self.ensure_by(
                TransferRecord, "learners.TransferRecord",
                {
                    "learner": learners[(index - 1) % len(learners)],
                    "transfer_date": date(2026, 5, index),
                    "reason": f"Sample transfer enquiry {index:02d}",
                },
                learner=learners[(index - 1) % len(learners)],
                from_institution=self.school,
                to_institution=destination,
                transfer_date=date(2026, 5, index),
                reason=f"Sample transfer enquiry {index:02d} - not applied to learner status.",
                status="CANCELLED" if index % 4 else "PENDING",
                recorded_by=User.objects.filter(role=Roles.SCHOOL_ADMIN, institution=self.school).first(),
            )

    def seed_snapshots(self, teachers):
        average = ExamResult.objects.filter(institution=self.school).aggregate(Avg("score"))["score__avg"]
        attendance = AttendanceRecord.objects.filter(institution=self.school).count()
        for index, kind in enumerate([
            "ATTENDANCE", "PERFORMANCE", "COMPETENCY", "LEARNER", "CLASS",
        ] * 3, start=1):
            self.ensure_by(
                ReportSnapshot, "reports.ReportSnapshot",
                {"institution": self.school, "title": f"Sample Snapshot {index:02d}"},
                institution=self.school,
                title=f"Sample Snapshot {index:02d}",
                report_type=kind,
                period_label="Sample Term 1 2026",
                data={
                    "sample_data": True,
                    "attendance_records": attendance,
                    "average_exam_score": round(float(average or 0), 2),
                    "note": "Fictional figures generated by seed_sample_data.",
                },
                generated_by=teachers[index % len(teachers)].user,
            )

    def seed_fees(self, learners, terms, classes, teachers):
        structures = []
        for index in range(1, 13):
            structure = self.ensure(
                FeeStructure, "fees.FeeStructure",
                {"reference": f"SMP-FEE-{index:04d}"},
                institution=self.school,
                name=f"Sample Fee Structure {index:02d}",
                term=terms[(index - 1) % len(terms)],
                school_class=classes[(index - 1) % len(classes)],
                amount=Decimal(1000 + index * 250),
                due_date=date(2026, 2 + (index % 9), 5 + (index % 20)),
                is_active=index <= 10,
            )
            structures.append(structure)

        invoices = []
        for index in range(1, 13):
            learner = learners[(index - 1) % len(learners)]
            due = Decimal(2000 + index * 500)
            invoice = self.ensure(
                FeeInvoice, "fees.FeeInvoice",
                {"reference": f"SMP-INV-{index:04d}"},
                institution=self.school,
                learner=learner,
                fee_structure=structures[(index - 1) % len(structures)],
                amount_due=due,
                issue_date=date(2026, 1, 6 + index),
                due_date=date(2026, 3, 6 + index),
            )
            invoices.append(invoice)

        for index, invoice in enumerate(invoices, start=1):
            amount = invoice.amount_due if index % 3 == 0 else invoice.amount_due / 2
            self.ensure(
                Payment, "fees.Payment",
                {"reference": f"SMP-PAY-{index:04d}"},
                institution=self.school,
                invoice=invoice,
                amount=amount,
                method=["CASH", "BANK", "MOBILE", "OTHER"][index % 4],
                paid_at=timezone.make_aware(
                    datetime.combine(date(2026, 2, 1 + index), time(10, index % 60))
                ),
                recorded_by=teachers[index % len(teachers)].user,
                notes=f"Sample payment {index:02d} recorded for testing only.",
            )

    def seed_approval(self, textbooks, teachers):
        admin = User.objects.filter(
            role=Roles.SCHOOL_ADMIN, institution=self.school
        ).first() or teachers[0].user
        statuses = [
            "DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED",
            "CHANGES_REQUESTED", "PUBLISHED",
        ]
        requests = []
        # 21 requests guarantee at least 10 recorded decisions after the
        # status cycle below, while keeping several live draft/review states.
        for index in range(1, 22):
            request = self.ensure(
                ApprovalRequest, "approval.ApprovalRequest",
                {"reference": f"SMP-APR-{index:04d}"},
                institution=self.school,
                title=f"Sample Approval Request {index:02d}",
                summary="Internal review sample. Not submitted to KICD and not an official approval.",
                content_type="TEXTBOOK" if index % 2 else "RESOURCE",
                textbook=textbooks[(index - 1) % len(textbooks)] if index % 2 else None,
                status=statuses[(index - 1) % len(statuses)],
                submitted_by=teachers[index % len(teachers)].user,
                reviewed_by=admin if index % 3 else None,
                submitted_at=timezone.now() if index % 3 else None,
                reviewed_at=timezone.now() if index % 5 == 0 else None,
                kicd_reference=f"SMP-INTERNAL-{index:03d}",
                due_date=date(2026, 11, 10 + (index % 19)),
            )
            requests.append(request)
            for check_index, label in enumerate(
                ["Curriculum alignment checked", "Language reviewed"], start=1
            ):
                self.ensure(
                    ApprovalChecklistItem, "approval.ApprovalChecklistItem",
                    {"reference": f"SMP-ACL-{index:02d}-{check_index}"},
                    institution=self.school,
                    request=request,
                    label=f"{label} {index:02d}",
                    is_met=(index + check_index) % 3 != 0,
                    notes="Sample check generated by seed_sample_data.",
                )
            decision = {
                "APPROVED": "APPROVE",
                "REJECTED": "REJECT",
                "CHANGES_REQUESTED": "REQUEST_CHANGES",
                "PUBLISHED": "APPROVE",
            }.get(request.status)
            if decision:
                self.ensure(
                    ApprovalDecision, "approval.ApprovalDecision",
                    {"reference": f"SMP-APD-{index:04d}"},
                    institution=self.school,
                    request=request,
                    decision=decision,
                    notes="Sample internal decision recorded for testing only.",
                    decided_by=admin,
                    reference_to_source=f"SMP-INTERNAL-{index:03d}",
                )

    def seed_kemis(self, teachers):
        datasets = [row[0] for row in [
            ("LEARNERS", "Learners"), ("TEACHERS", "Teachers"),
            ("INSTITUTION", "Institution"), ("ENROLLMENT", "Enrollment"),
            ("ATTENDANCE", "Attendance"), ("RESULTS", "Results"),
        ]]
        for index in range(1, 13):
            self.ensure(
                KemisExport, "kemis.KemisExport",
                {"reference": f"SMP-KEM-{index:04d}"},
                institution=self.school,
                dataset=datasets[(index - 1) % len(datasets)],
                format="CSV" if index % 2 else "JSON",
                status="READY",
                filters={"sample_data": True, "term": "2026-Term-1"},
                record_count=10 + index,
                generated_by=teachers[index % len(teachers)].user,
                generated_at=timezone.now(),
                payload="Sample local staging file. Check the official KEMIS template before any submission.",
                notes="Never transmitted; column names are a local approximation.",
            )
        mappings = [
            ("LEARNERS", "user.full_name", "LEARNER_NAME"),
            ("LEARNERS", "admission_number", "ADMISSION_NO"),
            ("LEARNERS", "assessment_number", "ASSESSMENT_NO"),
            ("LEARNERS", "gender", "GENDER"),
            ("LEARNERS", "class_room.name", "CLASS_NAME"),
            ("TEACHERS", "user.full_name", "TEACHER_NAME"),
            ("TEACHERS", "staff_number", "STAFF_NO"),
            ("TEACHERS", "employment_type", "EMPLOYMENT_TYPE"),
            ("INSTITUTION", "name", "SCHOOL_NAME"),
            ("INSTITUTION", "county", "COUNTY"),
            ("ENROLLMENT", "status", "ENROLMENT_STATUS"),
            ("RESULTS", "score", "SCORE"),
        ]
        for index, (dataset, source, target) in enumerate(mappings, start=1):
            self.ensure(
                KemisFieldMapping, "kemis.KemisFieldMapping",
                {"reference": f"SMP-KFM-{index:04d}"},
                dataset=dataset,
                source_field=source,
                target_column=target,
                is_required=index <= 8,
                is_active=True,
                ordering=index,
                notes="Sample local mapping; verify against the current official template.",
            )

    def seed_tutor(self, learners, teachers):
        admin = User.objects.filter(
            role=Roles.SCHOOL_ADMIN, institution=self.school
        ).first() or teachers[0].user
        conversations = []
        for index in range(1, 13):
            started_by = learners[(index - 1) % len(learners)].user if index > 2 else admin
            conversation = self.ensure(
                TutorConversation, "tutor.TutorConversation",
                {"reference": f"SMP-TUT-{index:04d}"},
                institution=self.school,
                title=f"Sample Tutor Conversation {index:02d}",
                learner=learners[(index - 1) % len(learners)],
                started_by=started_by,
                status="ACTIVE" if index <= 10 else "ARCHIVED",
            )
            conversations.append(conversation)
            self.ensure(
                TutorMessage, "tutor.TutorMessage",
                {"reference": f"SMP-TMQ-{index:04d}"},
                institution=self.school,
                conversation=conversation,
                role=TutorMessage.Role.USER,
                body=f"Sample question {index:02d} about whole numbers?",
                created_by=started_by,
            )
            self.ensure(
                TutorMessage, "tutor.TutorMessage",
                {"reference": f"SMP-TMA-{index:04d}"},
                institution=self.school,
                conversation=conversation,
                role=TutorMessage.Role.TUTOR,
                body="Use the stored learning outcome: represent and compare whole numbers up to 10,000.",
                sources=[{
                    "kind": "learning_outcome",
                    "code": f"SMP-LO-{index:02d}",
                    "label": f"Learning outcome {index:02d}",
                }],
                suggestions=["Try the linked practice activity."],
                created_by=started_by,
            )

    def seed_analytics_records(self, competencies, learners, teachers):
        datasets = [row[0] for row in AnalyticsSnapshot.DATASETS]
        for index in range(1, 13):
            self.ensure(
                AnalyticsSnapshot, "analytics.AnalyticsSnapshot",
                {"reference": f"SMP-ANA-{index:04d}"},
                institution=self.school,
                dataset=datasets[(index - 1) % len(datasets)],
                period=f"SMP-2026-T{(index % 3) + 1}-{index:02d}",
                payload={
                    "sample_data": True,
                    "note": "Fictional snapshot generated by seed_sample_data.",
                    "learners": 10 + index,
                },
                generated_by=teachers[index % len(teachers)].user,
                generated_at=timezone.now(),
            )
            rule = self.ensure(
                RemediationRule, "analytics.RemediationRule",
                {"reference": f"SMP-RMR-{index:04d}"},
                institution=self.school,
                name=f"Sample Remediation Rule {index:02d}",
                competency=competencies[(index - 1) % len(competencies)],
                mastery_below=Decimal("0.40") + Decimal(index % 4) / Decimal("10"),
                min_attempts=1 + (index % 3),
                action=["PRACTICE", "RESOURCE", "COURSE", "TEACHER_REVIEW"][index % 4],
                target_course=None,
                is_active=index <= 10,
                notes="Sample rule generated by seed_sample_data.",
            )
            self.ensure(
                RemediationTask, "analytics.RemediationTask",
                {"reference": f"SMP-RMT-{index:04d}"},
                institution=self.school,
                learner=learners[(index - 1) % len(learners)],
                rule=rule,
                competency=competencies[(index - 1) % len(competencies)],
                status=["OPEN", "ASSIGNED", "COMPLETED", "DISMISSED"][index % 4],
                evidence={"sample_data": True, "signal": "seeded_evidence"},
                due_date=date(2026, 12, 1 + index),
                assigned_to=teachers[index % len(teachers)].user if index % 4 == 1 else None,
            )

    def seed_audit_log(self, teachers):
        for index in range(1, 13):
            self.ensure_by(
                AuditLog, "core.AuditLog",
                {
                    "institution": self.school,
                    "action": "SAMPLE_SEEDED",
                    "entity_type": "SampleRecord",
                    "entity_id": f"SMP-{index:03d}",
                },
                institution=self.school,
                user=teachers[index % len(teachers)].user,
                action="SAMPLE_SEEDED",
                entity_type="SampleRecord",
                entity_id=f"SMP-{index:03d}",
                details={"sample_data": True, "note": "Generated by seed_sample_data."},
            )

    def report(self):
        self.stdout.write(self.style.SUCCESS("Sample data seeding complete."))
        self.stdout.write("All records are fictional and labelled with SMP- codes, sample_ usernames or SAMPLE text.")
        self.stdout.write(f"New records created this run: {sum(self.created.values())}")
        for label, count in sorted(self.created.items()):
            self.stdout.write(f"  {label}: +{count}")

        self.stdout.write("")
        self.stdout.write("Category counts (minimum 10 required):")
        low = []
        for label in TRACKED_MODELS:
            app_label, model_name = label.split(".")
            model = apps.get_model(app_label, model_name)
            count = model.objects.count()
            flag = "OK" if count >= 10 else "LOW"
            if count < 10:
                low.append(label)
            self.stdout.write(f"  {label}: {count} [{flag}]")
        if low:
            self.stdout.write(self.style.WARNING(f"Below minimum: {', '.join(low)}"))
