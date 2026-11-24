# Command reference (PowerShell)

Every command below is copied from a working folder. Check the folder before
you run a command: Django commands need `backend/`, npm commands need
`frontend/`, and the backup script needs the project root.

**Project root:** `C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms`

No passwords appear in this file. When a command asks for one, type it at the
prompt. Keep real values in the Git-ignored `.env` file only.

## 1. Move to the project root

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms"
```

## 2. Backend: prepare the virtual environment

**Working directory:** `...\kenyan-lms\backend`

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked by the execution policy, allow it for this terminal
session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

You can leave the environment active and use `python ...`, or skip activation
and call the interpreter directly. The direct form is used below because it
always works:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

To leave an activated environment, run `deactivate`.

## 3. Backend: checks and migrations

**Working directory:** `...\kenyan-lms\backend`

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py showmigrations institutions
```

`makemigrations --check --dry-run` must report **No changes detected** before
you commit a model change. If it reports changes, review them, generate the
migration normally (`manage.py makemigrations <app>`), and take a backup before
applying it.

**Rule:** never delete or recreate the `lms` database as a routine fix. Read
`docs/DATABASE_GUIDE.md` and `docs/BACKUP_AND_RESTORE.md` first.

The school-profile migration
`apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
was generated and applied after the backup at
`backups/lms_20261123_134452.sql`.

## 4. Backend: tests

**Working directory:** `...\kenyan-lms\backend`

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Focused tests used during the latest work:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/institutions/tests/test_institutions.py apps/accounts/tests/test_auth.py
.\.venv\Scripts\python.exe -m pytest apps/core/tests/test_reference_codes.py
```

The latest recorded results are in `docs/TESTING_CHECKLIST.md`. The final full
backend suite result is **95 passed**; do not replace it with an older result.

## 5. Backend: accounts

**Working directory:** `...\kenyan-lms\backend`

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py changepassword demo_admin
.\.venv\Scripts\python.exe manage.py changepassword demo_teacher
.\.venv\Scripts\python.exe manage.py changepassword demo_learner
.\.venv\Scripts\python.exe manage.py changepassword demo_guardian
.\.venv\Scripts\python.exe manage.py changepassword platform_admin
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py seed_sample_data
```

`changepassword` prompts twice; the typed value is not shown.
`createsuperuser` now defaults to role `SUPER_ADMIN`. Permissions still use the
`role` field, so change it explicitly when a different scope is needed:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from apps.accounts.models import User; u=User.objects.get(username='your_new_admin'); u.role='SCHOOL_ADMIN'; u.save(update_fields=['role'])"
```

For a single school, also set `u.institution`. `seed_sample_data` is add-only
and idempotent; see `docs/SAMPLE_DATA.md`. Never write a password into the
command or a document.

## 6. Backend: run the API

**Working directory:** `...\kenyan-lms\backend`

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Health check from another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health/
```

Expected: `"status":"ok"` and `"database":"connected"`.

## 7. Backend: production configuration check

**Working directory:** `...\kenyan-lms\backend`

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings_prod"
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py migrate --plan
```

The environment variable applies only to the current PowerShell session. To
return to local settings in that session:

```powershell
Remove-Item Env:DJANGO_SETTINGS_MODULE
```

This is a **check**, not a deployment. A WSGI/ASGI server, TLS termination,
backups and monitoring are still required. See
`docs/PRODUCTION_CONFIGURATION.md`.

## 8. Frontend

**Working directory:** `...\kenyan-lms\frontend`

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\frontend"
npm install
npm test
npm run build
npm run dev
npm audit --audit-level=moderate
```

`npm run dev` serves the app at <http://127.0.0.1:5173>. Staff pages are under
`/admin/...`; learner and guardian pages are under `/portal/...`.

`npm run build` writes `frontend/dist`, including the generated service worker
and PWA manifest. A Vite message about one chunk larger than 500 kB is a
warning, not a failure. The most recent build produced 7 PWA precache entries.

Use `npm ci` instead of `npm install` when you want to install exactly the
versions in `package-lock.json` (for example, on a build server).

## 9. Backup and restore

**Working directory:** project root

Read the script before running it — it explains how it uses `.env` and where
it writes the dump:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms"
Get-Content .\scripts\backup_database.ps1
& .\scripts\backup_database.ps1
```

The script reads `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` and `DB_PASSWORD`
from `.env`, then writes `backups\lms_YYYYMMDD_HHMMSS.sql`. No password is
typed into the command. The backup taken before the school-profile migration is
`backups\lms_20261123_134452.sql`.

Only read the restore script during normal work. Restoring overwrites data, so
do it only with a clear reason and a fresh backup:

```powershell
Get-Content .\scripts\restore_database.ps1
```

**Never delete or recreate the `lms` database as a routine fix.** Take a backup
before structural changes and read `docs/BACKUP_AND_RESTORE.md`.

## 10. Typical development session

Terminal 1:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Terminal 2:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\frontend"
npm run dev
```

Then open <http://127.0.0.1:5173> and sign in. `RoleHome` sends staff to
`/admin` and learners or guardians to `/portal`. Legacy root URLs such as
`/learners` and `/reports` redirect to the right side by role.
