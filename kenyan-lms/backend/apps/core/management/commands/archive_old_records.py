"""Archive old, inactive learner, teacher and guardian records.

This never deletes anything. It only sets ``is_archived`` and ``archived_at``
so historical data stays queryable while reports can exclude it. A dry run is
the default; pass ``--apply`` to write the changes.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.guardians.models import Guardian
from apps.learners.models import Learner, LearnerGuardian
from apps.teachers.models import Teacher

IDENTIFIERS = {
    "Learner": "admission_number",
    "Teacher": "staff_number",
    "Guardian": "guardian_number",
}


class Command(BaseCommand):
    help = "Mark eligible old records archived. Dry run by default; use --apply to write."

    def add_arguments(self, parser):
        parser.add_argument(
            "--before",
            required=True,
            help="ISO date (YYYY-MM-DD); only records created before this date are eligible.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the archive flags. Without this flag nothing is changed.",
        )

    def handle(self, *args, **options):
        try:
            cutoff = date.fromisoformat(options["before"])
        except ValueError as exc:
            raise CommandError("--before must be an ISO date (YYYY-MM-DD).") from exc

        active_learner_ids = Learner.objects.filter(
            is_archived=False, status="ACTIVE"
        ).values_list("pk", flat=True)

        candidates = {
            "Learner": Learner.objects.filter(
                created_at__date__lt=cutoff,
                is_archived=False,
                status__in=["ALUMNI", "TRANSFERRED"],
            ),
            "Teacher": Teacher.objects.filter(
                created_at__date__lt=cutoff,
                is_archived=False,
                is_active=False,
            ),
            # Guardians with only left/archived learners. Guardians with no link
            # at all are left alone: they may still be awaiting verification.
            "Guardian": Guardian.objects.filter(
                created_at__date__lt=cutoff,
                is_archived=False,
                learner_links__isnull=False,
            ).exclude(learner_links__learner_id__in=active_learner_ids).distinct(),
        }

        if not options["apply"]:
            self.stdout.write("DRY RUN - no records changed. Pass --apply to write.")
        for label, queryset in candidates.items():
            field = IDENTIFIERS[label]
            rows = list(queryset.values_list("pk", field))
            self.stdout.write(f"{label}: {len(rows)} eligible")
            for pk, identifier in rows:
                self.stdout.write(f"    {pk} {identifier}")
            if options["apply"] and rows:
                with transaction.atomic():
                    now = timezone.now()
                    model = {"Learner": Learner, "Teacher": Teacher, "Guardian": Guardian}[label]
                    model.objects.filter(pk__in=[pk for pk, _ in rows]).update(
                        is_archived=True, archived_at=now
                    )
                    for pk, identifier in rows:
                        AuditLog.objects.create(
                            action="record.archived",
                            entity_type=label,
                            entity_id=str(pk),
                            details={
                                "identifier": identifier,
                                "created_before": cutoff.isoformat(),
                            },
                        )
                self.stdout.write(f"Archived {len(rows)} {label} record(s).")

        if options["apply"]:
            self.stdout.write("Archive complete. No records were deleted.")
