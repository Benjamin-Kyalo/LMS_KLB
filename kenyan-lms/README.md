# Kenyan Digital Learning Ecosystem (KLB LMS)

An integrated, offline-friendly digital education platform for Kenyan
learning institutions. It combines a **Learning Management System (LMS)**,
a **Student Information System (SIS)** and a **Digital Content and
Publishing Platform** in one maintainable codebase.

> **Location:** `C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms`
> This folder sits inside the GitHub Desktop repository, so changes sync
> through GitHub Desktop.

## Current status

| Phase | Status |
|---|---|
| Phase 0 — Assessment and planning | Complete |
| Phase 1 — System foundation | Complete |
| Phase 2 — SIS | Complete |
| Phase 3 — LMS | Core complete; dedicated module/lesson/question forms added |
| Phase 4 — Kenyan CBE | Complete (configurable structures) |
| Phase 5 — Digital publishing | Foundation complete; chapter/resource forms added |
| Phase 6 — Parent & administration | Mostly implemented (foundation) |
| Phase 7 — Offline & mobile | Foundation only; offline queue exists, automatic conflict resolution pending |
| Phase 8 — Advanced features | Partial: reference numbers, charts, smoke tests and hardening added; analytics/remediation pending |
| Phase 9 — Production & handover | Not complete: production settings and docs ready; no deployment, load test or security review |

Phases 0–6 are mostly implemented; Phase 7 is a foundation, Phase 8 is partial
and Phase 9 is not complete. **This project is not 100% complete.** See
`docs/HANDOVER_REPORT.md` for the honest status.

## Two sides of the app

- Staff (platform admins, school admins, teachers, content managers) use
  `/admin/...` with `DashboardLayout`.
- Learners and guardians use `/portal/...` with `PortalLayout`.
- `/` is the public homepage, with no administrator link. A role selector shows
  the rights and content for each audience; footer text and role previews are
  editable in `frontend/src/config/publicSite.js`. Sign-in and registration send
  each role to the right side. Old root URLs such as `/learners`, `/courses` and
  `/reports` still redirect by role.

## Technology stack

- **Frontend:** React 19 + Vite 8 (JavaScript, HTML5, CSS3)
- **Backend:** Python 3.13 + Django 6.1 + Django REST Framework 3.18
- **Database:** PostgreSQL 18 (database name: `lms`)
- **Architecture:** modular monolith, 14 Django apps, one React SPA
- **Configuration:** environment variables in a local `.env` file
- **PWA:** service worker via `vite-plugin-pwa`

## Quick start

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\frontend"
npm run dev
```

Open <http://127.0.0.1:5173>. Full command list with working directories:
`docs/COMMANDS.md`.

## Demo logins

Run `python manage.py seed_demo` once from `backend/` to create demo accounts.

| Username | Role |
|---|---|
| `demo_admin` | School administrator |
| `demo_teacher` | Teacher |
| `demo_learner` | Learner |
| `demo_guardian` | Guardian |
| `platform_admin` | Platform super administrator |

Passwords are deliberately not printed here. To set a password you control,
run `.\.venv\Scripts\python.exe manage.py changepassword <username>` from
`backend/` and type it twice at the prompt. To create a fresh administrator,
use `.\.venv\Scripts\python.exe manage.py createsuperuser`, then set its role
as described in `docs/ADMIN_ACCESS.md`.

## School profile

School admins can edit their own school at `/admin/school` through
`GET/PATCH /api/institutions/mine/`. Fields include phone, email, website,
motto and a JPG/PNG/WebP logo up to 2 MB. Logo upload needs an internet
connection. The URL is returned as `institution_logo` by `/api/auth/me/` and
shown in both layouts. Learners and guardians may read school details but may
not PATCH the profile (HTTP 403). The migration
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
was applied after the backup `backups/lms_20261123_134452.sql`.

## Tests actually run

Final consolidated round (23 November 2026):

- Frontend: `npm test -- --run` → **45 passed across 18 files**
- Frontend production build: `npm run build` → success; one chunk >500 kB is a
  Vite warning, not a failure; PWA generated **7** precache entries
- Dependency audit: `npm audit --audit-level=moderate` → **0 vulnerabilities**
- Backend: `manage.py check` → clean; `makemigrations --check --dry-run` → no changes
- Backend full suite: `python -m pytest -q` → **50 passed**
- Production config: `check --deploy` with `config.settings_prod` → no issues
- Sample data: `seed_sample_data` → all categories `[OK]`, 0 new records on rerun
- Live API: `/api/health/` returned `status: ok`, `database: connected`
- Browser: 1440×900 and emulated 390×844 checks passed for public, admin and
  portal routes with no console errors and no horizontal overflow

See `docs/TESTING_CHECKLIST.md` for the full record and the remaining
limitations. Phases 7–9 are not claimed as complete.

## Important rules

1. Never commit `.env` or any real password.
2. Never delete or recreate the `lms` database as a routine fix.
3. Take a backup before structural database changes.
4. Do not claim a feature works until its tests have actually run.

## Documentation index

See `docs/README.md`.
