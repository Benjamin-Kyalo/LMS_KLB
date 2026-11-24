# Handover report

**Date:** 23 November 2026
**Project:** Kenyan Digital Learning Ecosystem (KLB LMS)
**Repository:** `https://github.com/Benjamin-Kyalo/LMS_KLB.git` (branch `main`)
**Working folder:** `C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms`

---

## 1. What was delivered

A working, integrated education platform combining an LMS, a Student
Information System and a digital publishing library. It is a modular monolith:
14 Django apps behind one REST API, consumed by one React single-page app,
backed by PostgreSQL `lms`.

| Deliverable | Where | State |
|---|---|---|
| Research report + Word document | repo root (`Kenyan_Digital_Learning_Ecosystem_Strategy_Report.*`) | Complete |
| Django backend + 14 apps | `backend/` | Complete |
| PostgreSQL schema + migrations | `backend/apps/*/migrations/` | Applied to `lms` |
| React 19 + Vite 8 frontend | `frontend/` | Complete |
| Public homepage and role-based auth | `frontend/src/pages/Home.jsx`, `Login.jsx`, `Register.jsx`, `AdminSignup.jsx`, `frontend/public/images/`, `frontend/public/hero-learning.svg`, `docs/ASSET_CREDITS.md` | Complete; photographed hero/workspaces, original insights section, interactive role access preview, sparse links, admin portal not advertised publicly |
| Editable public content | `frontend/src/config/publicSite.js`, `docs/PUBLIC_SITE_CONTENT.md` | Complete; footer text and role previews live in one config file with optional runtime override |
| PWA manifest + generated service worker | `frontend/public/`, `frontend/dist/sw.js` | Complete |
| Offline mutation queue | `frontend/src/services/offlineQueue.js` | Core built; earlier browser replay verified. Latest browser sweep covered rendered pages only, not offline replay |
| Demo data command | `backend/apps/core/management/commands/seed_demo.py` | Complete |
| Backup / restore / environment scripts | `scripts/` | Complete |
| Central reference-number generator | `backend/apps/core/codes.py` | Complete, tested |
| Production settings | `backend/config/settings_prod.py` | Complete, final `check --deploy` clean |
| Two UI sides | `frontend/src/App.jsx`, `RoleHome.jsx`, `DashboardLayout.jsx`, `PortalLayout.jsx` | Implemented and browser-verified for staff, learner and guardian routes |
| School self-service profile | `backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`, `frontend/src/pages/SchoolProfile.jsx` | Migration applied after backup; API and focused tests passed |
| Documentation set (22 Markdown files including this report) | `docs/` | Written/updated |
| Automated tests | `backend/apps/*/tests/`, `frontend/src/**/*.test.js` | Final backend **95 passed**; final frontend **52 passed across 19 files**; build and audit clean |
| Invitation-only admin signup | `backend/apps/accounts/`, `frontend/src/pages/AdminSignup.jsx` | Single-use expiring server-side token; no public admin registration |
| Backend-enforced RBAC | `backend/apps/core/permissions.py`, `backend/apps/core/viewsets.py`, `frontend/src/components/ManagedResourcePage.jsx` | Write mixins on the API plus matching UI action flags; hierarchy and self-escalation tests pass |
| Labelled sample data | `backend/apps/core/management/commands/seed_sample_data.py`, `docs/SAMPLE_DATA.md` | Add-only, idempotent, every category ≥10, no passwords printed or stored |
| Admin list data tools | `frontend/src/hooks/useTableControls.js`, `frontend/src/components/TableTools.jsx`, `ResourcePage.jsx`, `Users.jsx`, `Learners.jsx`, `AdminInvitations.jsx` | Shared search, row-size control, refresh and pagination |

## 2. Phase status (honest)

| Phase | Status | Notes |
|---|---|---|
| 0 — Assessment and planning | Complete | Environment verified, research report written |
| 1 — System foundation | Complete | Settings, env, auth, roles, permissions, health check |
| 2 — SIS | Complete | People, structure, attendance, timetable, bulk import |
| 3 — LMS | Core complete | Courses, modules, lessons, progress, assignments, submissions, quizzes, exams; dedicated forms for modules/lessons/questions |
| 4 — Kenyan CBE | Complete | Version-aware frameworks, outcomes, competencies, rubrics, evidence |
| 5 — Digital publishing | Foundation complete | Textbooks, chapters, resources, exercises, licensing; chapter/resource forms added |
| 6 — Parent & administration | Mostly implemented | Guardian links, scoped reports, announcements, messages; the portal now has its own layout |
| 7 — Offline & mobile | Foundation plus safe first-pass recovery | PWA shell, network-first API cache, offline banner and IndexedDB write queue exist. A stale update is now replayed once against the server's current `updated_at`; unresolved conflicts stay in the queue with manual retry/discard. Capacitor wrapper scaffolding was added, but no signed native app, fresh offline browser replay or physical-device test was performed |
| 8 — Advanced features | Partial | Reference numbering, charts and dashboard links plus a fee ledger, internal KICD-style review workflow, local KEMIS staging, bounded deterministic tutor and analytics/remediation rules are in place. Scale notifications, official KICD submission, official KEMIS transmission, LTI marketplace and optional hosted AI are not implemented |
| 9 — Production & handover | Not complete | Docs, tests and production settings are ready. **No production deployment, load test or third-party security review.** |

Do not describe Phases 7–9 as finished. Phases 0–6 are mostly implemented,
not a claim of 100% completion.

### Two UI sides and school profile

- `/` is a public homepage with a locally hosted hero photograph, three
  photographed workspace cards, a facts strip, an original progress/insights
  section and an interactive role selector. Selecting a role reveals the rights
  and content for that role and its single workspace link. The three static
  taglines (“Your role decides…”, “Each workspace uses the same records…”, and
  “Role-based access · Offline-friendly · One shared school database”) and the
  public sample-data notice were removed at the user's request. Duplicate “Quick
  access”, repeated workspace sign-in, repeated section anchors and footer auth
  links were also removed. It does not advertise the internal administration
  portal. Public registration offers learner, guardian and teacher accounts only.
  Footer text and role previews are editable in
  `frontend/src/config/publicSite.js` (see `docs/PUBLIC_SITE_CONTENT.md`).
  Unsplash photographs and the original KLB SVG are credited in
  `docs/ASSET_CREDITS.md`.
- Staff pages are at `/admin/...` with `DashboardLayout`; learner and guardian
  pages are at `/portal/...` with `PortalLayout`. Sign-in routes by role and
  `RoleHome` redirects old root URLs such as `/learners`, `/courses` and
  `/reports` to the right side. `/admin/login` and invitation-only
  `/admin/signup` remain the dedicated administrator entry points.
- School administrators can read and edit only their own school through
  `GET/PATCH /api/institutions/mine/` at `/admin/school`. Learners and
  guardians may read school details but get HTTP 403 on PATCH.
- `Institution` now has `phone`, `email`, `website`, `motto` and `logo`. Logo
  uploads are multipart JPG/PNG/WebP, at most 2 MB, and need an internet
  connection. `GET /api/auth/me/` returns `institution_logo`, which both
  layouts display with `/mark.svg` as fallback.
- The migration
  `backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
  was applied after the backup `backups/lms_20261123_134452.sql`.
- Admin list pages now share search, row-size, refresh and pagination controls
  through `useTableControls.js` and `TableTools.jsx`. Role filters remain on
  the user page; all controls are client-side over institution-scoped API
  results.

## 3. Verification actually performed

### Latest verification round (final local pass)

| Check | Result |
|---|---|
| Frontend `npm test -- --run` | **52 passed across 19 files** |
| Frontend `npm run build` | Success; Vite reported one chunk over 500 kB (warning only); PWA generated **7** precache entries |
| Backend `manage.py check` | Clean, no issues |
| Backend `manage.py makemigrations --check --dry-run` | No changes detected |
| Backend `python -m pytest -q` | **95 passed** |
| Production `check --deploy` | No issues |
| `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| `seed_sample_data` | All categories `[OK]`; 0 new records on the final rerun |
| Live health / UI | API `status: ok`, `database: connected`; Vite UI HTTP 200 |
| Browser sweep | 10 CDP checks at 1440×900 and emulated 390×844 covered public auth/homepage, admin dashboard/lists/menus, learner and guardian portals, role gates and console; a later sweep at 390×844 also covered fees, approval, KEMIS, tutor, analytics and sync on the admin side and home, fees, remediation, tutor and sync on the portal side. All passed with no horizontal overflow or console errors |

The browser sweep used short-lived server-generated API tokens for the portal
roles so no password was typed, printed or stored. Earlier checks in the same
round covered all admin routes, report charts and legacy redirects. Screenshots
were captured but the agent could not perform a human visual design review;
verification was DOM, layout-metric and console based. The sweep did not
include a physical device, destructive form submissions, logo upload, fresh
offline replay or assistive-technology testing. See `docs/TESTING_CHECKLIST.md`.

### Earlier verification round (before the newest school-profile changes)

All commands in the table below were run on 23 November 2026 in this folder.
They remain historical results, not a new full-suite result.

| Check | Result |
|---|---|
| `python manage.py check` | No issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python manage.py migrate` | All migrations applied |
| `python -m pytest` | **28 passed, 52 subtests passed** |
| Production: `DJANGO_SETTINGS_MODULE=config.settings_prod ... check --deploy` | No issues |
| `npm test` | **8 passed** (3 files, Vitest 4.1.12) |
| `npm run build` | Success; PWA service worker generated (6 precache entries) |
| `npm audit --audit-level=moderate` | **0 vulnerabilities** after pinning Vitest 4.1.12 and adding glob/minimatch overrides |
| `GET /api/health/` | `status: ok`, `database: connected` |
| `POST /api/auth/login/` | Token returned, role `SCHOOL_ADMIN` |
| `GET /api/learners/` | Demo learners rendered |
| `GET /api/reports/dashboard/` | Attendance and average score rendered |
| All list endpoints smoke test | Every endpoint returned HTTP < 500 |
| Browser: login → dashboard (before the `/admin` split) | Worked; no console errors at that time. The split was verified in the final round above |
| Browser: nested content pages (before the `/admin` split) | Modules, lessons, questions, chapters and resources all rendered at their old root URLs; no console errors |
| Browser: offline queue | Failed POST queued; reconnect + Sync now replayed it and refreshed the table |
| Browser: auto admission number | Blank admission field accepted; table showed `ADM-DEMO01-002` |
| API: auto admission number | POST without a code returned `ADM-DEMO01-001` |

Full detail: `docs/TESTING_CHECKLIST.md`.

## 4. Demo accounts

Run `python manage.py seed_demo` from `backend/` once if data is missing.

| Username | Role |
|---|---|
| `demo_admin` | School administrator |
| `demo_teacher` | Teacher |
| `demo_learner` | Learner |
| `demo_guardian` | Guardian |
| `platform_admin` | Platform super administrator |

Passwords are intentionally not reproduced in this report. Set or reset one
locally with `python manage.py changepassword <username>` from `backend/`, or
create a new administrator with `python manage.py createsuperuser`.
See `docs/ADMIN_ACCESS.md`.

Browser and API checks added harmless demo learners such as `Test Learner`,
`Offline Learner`, `Auto Code` and `Ui Generated`. Remove or reseed the demo
database before a real deployment.

## 5. How to run

```powershell
# Terminal 1 - API
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Terminal 2 - UI
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\frontend"
npm run dev
```

Open <http://127.0.0.1:5173>. Full setup: `docs/INSTALLATION_GUIDE.md`.
Production configuration: `docs/PRODUCTION_CONFIGURATION.md`.

## 6. Known limitations (must be disclosed)

1. **Offline conflict recovery is first-pass only.** A stale write is replayed
   once with the server's current `updated_at` as `If-Match`. If the server
   version moved again, or no version was supplied, the change stays in the
   queue for a human to retry, rebase again or discard. No local edit is
   silently overwritten.
2. **No production deployment.** Production settings exist and pass
   `check --deploy`, but no public server, load test, monitoring or third-party
   security review has been performed.
3. **Frontend test coverage is narrower than the full UI.** Utilities, guards,
   dashboard, reports, resource pages, public pages and the offline queue are
   covered; not every CRUD dialog or destructive action has an automated test.
4. **Automated accessibility audit passed** on the public homepage
   (Lighthouse accessibility **1.00**, Best Practices **1.00**, SEO **1.00**)
   after darkening muted text and fixing metadata. An assistive-technology
   audit and human visual review are still outstanding.
5. **Generated textbook ISBNs are catalogue IDs**, not publisher-issued ISBNs.
   Supply the real ISBN when one exists.
6. Edge caching for PWA API responses is network-first. The new modules are
   deliberately bounded: fees are a school-office ledger with no gateway,
   KICD-style review is internal only, KEMIS export is local staging only, and
   the tutor is deterministic and curriculum-grounded unless an HTTP provider
   is explicitly configured.
7. A physical mobile-device pass and a fresh offline replay after the newest UI
   changes were not performed. Chrome's 390×844 emulation was checked. The
   Capacitor wrapper is scaffolding only: no signed APK/IPA, native plugins or
   store artefacts were produced.
8. Invitation tokens are high-entropy server-side tokens with expiry,
   single-use marking and revocation; they are stored in the database so an
   authorised admin can copy them later, and they are **not** HMAC-signed or
   hashed. UI wording was corrected from “signed invitation” to “secure,
   single-use invitation token”. Treat the token like a credential.
9. Browser verification was DOM, layout-metric and console based. Screenshots
   were captured, but no human visual design review or assistive-technology
   audit was performed by this agent.
10. Phase 7 remains a foundation despite the safe rebase helper; Phase 8 is
   partial and Phase 9 is not complete. This project is not 100% complete.

## 7. Security posture

- Passwords exist only in `.env` (Git-ignored); `.env.example` is the template.
- Institution isolation is enforced in one shared queryset mixin. The mixin
  also overrides client-supplied `institution` values on create and update.
  Tests cover users, courses, modules, cross-school 404s and all list endpoints.
- DRF token auth; logout deletes the token; password change and reset exist.
- Admin-created learner/teacher/guardian accounts are created with unusable
  passwords; the account owner sets a password through the reset flow. Public
  registration uses the password chosen on the form. No generated password is
  displayed or stored.
- Django 6 `MAILERS` replaces deprecated `EMAIL_*` settings; no deprecation
  warning remains in the test run.
- Production settings enforce explicit hosts, CORS, TLS redirects, HSTS and
  secure cookies.
- This is **not** a substitute for a professional security review.

## 8. Recommended next steps

1. Add full end-to-end tests with Playwright, including real login and CRUD
   submissions.
2. Replay a fresh offline mutation and a forced conflict on a real device, then
   confirm the manual retry/discard path still behaves as documented.
3. Consider hashing invitation tokens and showing them only once at issue time.
4. Take a backup (`scripts/backup_database.ps1`) before any further schema work.
5. Deploy behind a reverse proxy with TLS using `config.settings_prod`.
6. Run load testing, monitoring and an independent security review.
7. Do not commit or push unless explicitly asked; GitHub Desktop sync is
   expected once the user approves the changes.

## 9. Documentation index

Start at `docs/README.md`. Key guides: `SYSTEM_OVERVIEW.md`,
`INSTALLATION_GUIDE.md`, `COMMANDS.md`, `PRODUCTION_CONFIGURATION.md`,
`REFERENCE_NUMBERING.md`, `REFERENCE_MODELS.md`, `DATABASE_GUIDE.md`,
`API_DOCUMENTATION.md`, `USER_GUIDE.md`, `ADMIN_GUIDE.md`,
`ADMIN_ACCESS.md`, `TROUBLESHOOTING.md`, `BACKUP_AND_RESTORE.md`,
`FILE_STRUCTURE_GUIDE.md`, `DESIGN_SYSTEM.md`, `TESTING_CHECKLIST.md`,
`MILESTONES_AJ.md`.
