# Backup and restore

## Golden rules

1. Back up **before** structural database changes.
2. Restore into a **new** database, never over the live one.
3. Keep `.env` and backups out of Git. Local `.env` remains Git-ignored and owner-managed;
   no secret is in source control.
4. `backups/` is Git-ignored because dumps contain password hashes and PII.
   Encrypt dumps and store them off-host.
5. Test the restore procedure occasionally, not only during a crisis.

## Backup

From the project root:

```powershell
.\scripts\backup_database.ps1
```

Optional destination:

```powershell
.\scripts\backup_database.ps1 -OutDir "D:\backups\lms"
```

The script reads credentials from `.env` and produces a plain SQL file named
`lms_yyyyMMdd_HHmmss.sql` using `pg_dump`.

## Restore into a new database

```powershell
.\scripts\restore_database.ps1 -BackupFile ".\backups\lms_20261123_120000.sql" -NewDbName "lms_restored"
```

The script **refuses** to overwrite an existing database. To use the restored
copy, change `DB_NAME=lms_restored` in `.env` and restart Django.

## Manual commands (if you prefer)

```powershell
$env:PGPASSWORD="your-password"
$bin="C:\Program Files\PostgreSQL\18\bin"
& "$bin\pg_dump.exe" -h 127.0.0.1 -U postgres -d lms -f backup.sql
& "$bin\createdb.exe" -h 127.0.0.1 -U postgres lms_restored
& "$bin\psql.exe" -h 127.0.0.1 -U postgres -d lms_restored -f backup.sql
```

## What else to back up

- `.env` (store it securely, separately)
- `backend/media/` (uploaded files)
- The repository itself (GitHub Desktop handles this)

## Current state and pending work

An existing database dump is kept at
`C:\Users\Admin IT\AppData\Local\Temp\opencode\lms-backup.dump`.

A least-privilege PostgreSQL role named `lms_app` has been created, but the
application still connects with the owner-managed credentials in `.env`.
Switching the app over to `lms_app` is **pending**, not done.

Cleanup completed just now, with backups: two unreferenced 800×450 placeholder
PNGs were moved to
`C:\Users\Admin IT\AppData\Local\Temp\opencode\orphan-media-backup`; user
`klb_user` (id 112), its onboarding profile and verified guardian link #33 were
removed after approval, and a JSON snapshot (password hash omitted) was saved
to `C:\Users\Admin IT\AppData\Local\Temp\opencode\deleted-records-backup.json`.
Five teachers with no approval record are pre-existing demo records awaiting
onboarding and were intentionally left alone.

`scripts/verify_backup.ps1 -Input <dump>` performs a restore test by loading the
dump into a unique throwaway database, running `manage.py check`, reading record
counts and dropping the temporary database. It is available now but must be
scheduled to make the restore test automated. `scripts/reporting_views.sql` and
the dry-run-by-default `archive_old_records` management command are also ready;
see `docs/DATA_LIFECYCLE.md`.

Still **pending** (not done): scheduling the restore test, executing an actual
archive/partition of old academic years, applying and refreshing the reporting
views in production, and the least-privilege `lms_app` switchover above.

## Verification after restore

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py shell -c "from apps.learners.models import Learner; print(Learner.objects.count())"
```
