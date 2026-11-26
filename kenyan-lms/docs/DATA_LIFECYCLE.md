# Data lifecycle

This document covers archiving, reporting views, backups and migration safety.
All commands below are **opt-in**: none of them delete records or change the
live database unless you explicitly run them with the indicated flags.

## Archiving old people records

`Learner`, `Teacher` and `Guardian` have `is_archived` and `archived_at`
fields. Archiving keeps the rows in place so historical attendance, results
and fees remain intact; reports simply filter on `is_archived = FALSE`.

Preview what would be archived (no writes):

```bash
cd backend
python manage.py archive_old_records --before 2026-01-01
```

Eligibility rules:

- **Learners** created before the cutoff whose status is `ALUMNI` or `TRANSFERRED`.
- **Teachers** created before the cutoff whose `is_active` is false.
- **Guardians** created before the cutoff who have at least one link, but no
  link to a current active learner. Guardians with no links are left alone.

Apply the same selection and write an audit row per record:

```bash
python manage.py archive_old_records --before 2026-01-01 --apply
```

The operation is wrapped in a transaction and is idempotent: already-archived
records are skipped. Review the dry-run output before using `--apply`.

## Academic-year partitioning (planned)

Old academic-year data (attendance, assessment attempts, fee ledger entries)
will eventually be partitioned by year rather than deleted. The intended
sequence, requiring a maintenance window and a verified backup:

1. Take and verify a fresh backup (`scripts/backup_postgres.ps1`, then
   `scripts/verify_backup.ps1`).
2. Inventory row counts per academic year and agree a retention period with
   the institution.
3. Add range partitions on the year key, starting with the oldest closed year.
4. Move closed-year rows into their partition; keep current and prior years in
   the active table.
5. Re-run `python manage.py check` and the full test suite against a restored
   copy before switching the application over.

Nothing in this sequence is automated yet. Do not partition live tables until
the restore test has been proven in the target environment.

## Reporting views

`scripts/reporting_views.sql` creates three optional materialized views:

- `mv_enrolment_summary` — learners per institution, active and archived.
- `mv_fee_collection` — payment count and total collected per institution.
- `mv_assessment_completion` — attempts, completions and average score.

The script is not a Django migration. Run it deliberately, after a backup:

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f scripts/reporting_views.sql
```

Refresh without blocking readers:

```sql
SELECT refresh_reporting_views();
```

## Backup and restore verification

- `scripts/backup_postgres.ps1` writes a custom-format dump.
- `scripts/verify_backup.ps1 -Input <dump>` restores the dump into a unique
  throwaway database, runs `manage.py check`, reads a few counts, then drops
  the throwaway database. It never targets the live database.
- `scripts/create_app_db_role.sql` prepares a least-privilege `lms_app` role.
  That role exists locally, but the application still uses owner-managed
  credentials; the switchover remains an environment task.

An automated, scheduled restore test is still pending. Until it exists, run
`verify_backup.ps1` manually after every production backup.

## Migration lock planning

Schema changes take short locks on the affected tables. For production:

1. Preview SQL with `python manage.py sqlmigrate <app> <migration>` during
   planning and redistribute large backfills as separate data migrations.
2. Schedule a maintenance window; set a short `lock_timeout` on the migration
   session so a busy table fails fast instead of queueing writers.
3. Verify a recent backup, apply migrations, then run `manage.py check` and a
   smoke test of the admin and public pages.
4. Keep the rollback path explicit: restore from the verified dump if a
   migration cannot be completed. Django migrations do not automatically
   reverse destructive data changes.

See `docs/BACKUP_AND_RESTORE.md` and `docs/DATABASE_GUIDE.md` for the current
backup state and transactional write behavior.
