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

- Staff (`SUPER_ADMIN`, `ADMIN`, custom roles with `admin.access`, teachers) use
  `/admin/...` with `DashboardLayout`.
- Learners and guardians use `/portal/...` with `PortalLayout`.
- `/` is the public homepage, with no administrator link. A role selector shows
  the rights and content for each audience. Administrators edit the header,
  footer, homepage, role cards, library and sign in wording at
  `/admin/appearance`; defaults stay in `frontend/src/config/publicSite.js`.
  Century Gothic is the preferred typeface with system fallbacks. Sign-in and
  registration send each role to the right side. Old root URLs such as
  `/learners`, `/courses` and `/reports` still redirect by role.

## Technology stack

- **Frontend:** React 19 + Vite 8 (JavaScript, HTML5, CSS3)
- **Backend:** Python 3.13 + Django 6.1 + Django REST Framework 3.18
- **Database:** PostgreSQL 18 (database name: `lms`)
- **Architecture:** modular monolith, 20 Django apps, one React SPA
- **Configuration:** environment variables in a local `.env` file
- **Delivery:** normal responsive web app; no service worker, PWA manifest, offline queue or native wrapper

## Quick start

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
$env:DJANGO_SETTINGS_MODULE="config.settings"
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
| `demo_admin` | `ADMIN` (institution administrator) |
| `demo_teacher` | `TEACHER` |
| `demo_learner` | `LEARNER` |
| `demo_guardian` | `GUARDIAN` |
| `platform_admin` | `SUPER_ADMIN` (demo username retained) |

Built-ins are `SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER` and
`GUARDIAN`. `SUPER_ADMIN` is globally unrestricted and can grant any role;
`ADMIN` is unrestricted in its own institution, can create/assign custom roles,
and cannot grant `SUPER_ADMIN` or create global institutions. `CUSTOM` is a named
role with picked capabilities and only enters `/admin` with `admin.access`; the
backend enforces the rest. Retired `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`,
`SCHOOL_ADMIN` and `CONTENT_MANAGER` accounts migrate to `ADMIN` with passwords
untouched. See `docs/USER_ROLES_JOURNEYS.md`.

Passwords are deliberately not printed here or changed by the role migration. To set a password you control,
run `.\.venv\Scripts\python.exe manage.py changepassword <username>` from
`backend/` and type it twice at the prompt. To create a fresh administrator,
use `.\.venv\Scripts\python.exe manage.py createsuperuser`, then set its role
as described in `docs/ADMIN_ACCESS.md`.

## School profile

Institution administrators (`ADMIN`) can edit their own school at `/admin/school` through
`GET/PATCH /api/institutions/mine/`. Fields include phone, email, website,
motto and a JPG/PNG/WebP logo up to 2 MB. Logo upload needs an internet
connection. The URL is returned as `institution_logo` by `/api/auth/me/` and
shown in both layouts. Learners and guardians may read school details but may
not PATCH the profile (HTTP 403). The migration
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
was applied after the backup `backups/lms_20261123_134452.sql`.

## Tests actually run

Latest recorded round — 24 November 2026 (theme manager and school-admin access):

- Frontend: `npm test -- --run` → **62 passed across 22 files**
- Frontend production build: `npm run build` → success; one chunk >500 kB is a
  Vite warning, not a failure; PWA generated **7** precache entries
- Dependency audit: `npm audit --audit-level=moderate` → **0 vulnerabilities**
- Backend: `manage.py check` → clean; `makemigrations --check --dry-run` → no changes
- Backend full suite: `python -m pytest -q` → **100 passed**
- Theme migration: backup `backups\lms_20261124_101534.sql` taken before
  `theming.0001_initial`; Ocean Blue Serenity remains active
- Browser: `/admin/theme` verified with school-admin access; no console errors

**Current palette status (25 November 2026):** the 24 November round above left
Ocean Blue Serenity active. `theming.0004_seed_and_activate_plum_harvest` has
since been applied locally: eight built-in palettes are seeded and Plum Harvest
(`plum-harvest`, from `color 7.png`) is active and the fresh-install default. See
`docs/DESIGN_SYSTEM.md`.

See `docs/TESTING_CHECKLIST.md` for the full verification history and remaining
limitations. Older delivery phase labels are recorded in `HANDOVER_REPORT.md`;
the new product roadmap is `docs/DEVELOPMENT_ROADMAP.md`. Do not mix the two
phase numbering schemes.

## Important rules

1. Never commit `.env` or any real password.
2. Never delete or recreate the `lms` database as a routine fix.
3. Take a backup before structural database changes.
4. Do not claim a feature works until its tests have actually run.

## Documentation index

See `docs/README.md`.
