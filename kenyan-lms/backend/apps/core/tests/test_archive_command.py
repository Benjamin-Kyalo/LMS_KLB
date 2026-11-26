"""The archive command is dry-run by default and never deletes records."""
from datetime import datetime, timezone as dt_timezone
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.core.models import AuditLog
from apps.guardians.models import Guardian
from apps.institutions.models import Institution, InstitutionType
from apps.learners.models import Learner, LearnerGuardian
from apps.teachers.models import Teacher

User = get_user_model()
OLD = datetime(2024, 1, 1, tzinfo=dt_timezone.utc)


class ArchiveCommandTests(TestCase):
    def setUp(self):
        kind = InstitutionType.objects.create(name="Archive Primary", code="ARC")
        self.school = Institution.objects.create(
            name="Archive School", code="ARS", institution_type=kind
        )
        self.cutoff = "2026-01-01"

    def person(self, username, role):
        return User.objects.create_user(
            username=username, password="StrongPass123!", role=role, institution=self.school
        )

    def backdate(self, instance):
        type(instance).objects.filter(pk=instance.pk).update(created_at=OLD)

    def test_dry_run_changes_nothing(self):
        learner = Learner.objects.create(
            user=self.person("archive_learner", "LEARNER"),
            institution=self.school, admission_number="ARL001", status="ALUMNI",
        )
        self.backdate(learner)
        output = StringIO()
        call_command("archive_old_records", before=self.cutoff, stdout=output)
        self.assertIn("DRY RUN", output.getvalue())
        learner.refresh_from_db()
        self.assertFalse(learner.is_archived)
        self.assertIsNone(learner.archived_at)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_apply_archives_only_eligible_records(self):
        old_left = Learner.objects.create(
            user=self.person("old_left", "LEARNER"), institution=self.school,
            admission_number="ARL002", status="TRANSFERRED",
        )
        active = Learner.objects.create(
            user=self.person("still_here", "LEARNER"), institution=self.school,
            admission_number="ARL003", status="ACTIVE",
        )
        self.backdate(old_left)
        self.backdate(active)

        old_teacher = Teacher.objects.create(
            user=self.person("old_teacher", "TEACHER"), institution=self.school,
            staff_number="ART001", is_active=False,
        )
        current_teacher = Teacher.objects.create(
            user=self.person("current_teacher", "TEACHER"), institution=self.school,
            staff_number="ART002",
        )
        self.backdate(old_teacher)
        self.backdate(current_teacher)

        guardian_user = self.person("old_guardian", "GUARDIAN")
        guardian = Guardian.objects.create(
            user=guardian_user, institution=self.school, guardian_number="ARG001"
        )
        self.backdate(guardian)
        LearnerGuardian.objects.create(learner=old_left, guardian=guardian)

        linked_guardian_user = self.person("active_guardian", "GUARDIAN")
        linked_guardian = Guardian.objects.create(
            user=linked_guardian_user, institution=self.school, guardian_number="ARG002"
        )
        self.backdate(linked_guardian)
        LearnerGuardian.objects.create(learner=active, guardian=linked_guardian)

        call_command(
            "archive_old_records", before=self.cutoff, apply=True, stdout=StringIO()
        )

        old_left.refresh_from_db()
        old_teacher.refresh_from_db()
        guardian.refresh_from_db()
        active.refresh_from_db()
        current_teacher.refresh_from_db()
        linked_guardian.refresh_from_db()

        self.assertTrue(old_left.is_archived)
        self.assertIsNotNone(old_left.archived_at)
        self.assertTrue(old_teacher.is_archived)
        self.assertTrue(guardian.is_archived)
        self.assertFalse(active.is_archived)
        self.assertFalse(current_teacher.is_archived)
        self.assertFalse(linked_guardian.is_archived)
        self.assertEqual(AuditLog.objects.filter(action="record.archived").count(), 3)

        # A second run is safe: already-archived rows are not processed again.
        call_command(
            "archive_old_records", before=self.cutoff, apply=True, stdout=StringIO()
        )
        self.assertEqual(AuditLog.objects.filter(action="record.archived").count(), 3)
        self.assertEqual(
            Learner.objects.filter(pk__in=[old_left.pk, active.pk]).count(), 2
        )
