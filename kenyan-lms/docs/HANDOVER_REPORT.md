# Handover report

**Date:** 24 November 2026
**Project:** Kenyan Digital Learning Ecosystem (KLB LMS)
**Repository:** `https://github.com/Benjamin-Kyalo/LMS_KLB.git` (branch `main`)
**Working folder:** `C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms`

---

## 0. Current direction — read this first

The product direction changed on 24 November 2026: this is a **normal web app
only**. The following were removed and must not be treated as delivered
features: the IndexedDB mutation queue, sync/conflict pages and banners,
service worker, PWA manifest, workbox precache, Capacitor configuration and the
`frontend/android` / `frontend/ios` directories. `npm run build` produces only
`index.html`, hashed CSS/JS assets, `robots.txt`, SVG marks and local images.

- Failed mutations now surface an error and remain unsaved. There is no local
  queue and no automatic replay. Uploads require a live connection.
- **Manual deployment step (not app code):** users who installed the old
  service worker need a one-release kill-switch — serve `/sw.js` with no-cache
  and an unregister/self-delete response, or have them clear site data.
- Authentication is Django session-cookie based: HttpOnly session cookie,
  readable CSRF cookie echoed as `X-CSRFToken`, identity/roles always re-read
  from `/api/auth/me/`. No `klb_token` or `klb_user` in `localStorage`.
- Security hardening includes retained PBKDF2 hashing, DB-backed login lockout
  plus scoped DRF throttles, trusted-proxy-aware `X-Forwarded-For`, one-hour
  single-use hashed reset records, session invalidation on password
  change/reset, security headers and production CSP, scoped
  content/assessment/course/learner/fee/attendance reads, upload magic-byte
  sniffing and generic health errors. Production fails closed without a
  separate `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins.
  Local `.env` remains Git-ignored and owner-managed; `backups/` is Git-ignored because dumps
  contain hashes/PII. No secret is in source control. See `SECURITY_AUDIT.md`.
- The homepage, sign-in and registration headings use an accessible canvas
  particle headline (`frontend/src/components/ParticleHeadline.jsx`) with
  palette-aware gradient colour, a soft halo, a left-to-right settle and a
  legible base `<h1>` beneath the particles. Hover repulsion is a gentle
  shimmer and reconstructs quickly, so headings stay clearly visible before
  and after pointer interaction. Reduced-motion support, responsive resize and
  cleanup are preserved.
- Buttons use a small local React/CSS interaction layer: `RollingLabel` keeps a
  real accessible label with a decorative duplicate for hover/focus motion;
  `AnimatedSubmitButton` adds press feedback to authentication submits; and
  `HoldToConfirmButton` gives destructive actions a hold fill with an Enter/Space
  fallback. Busy states use visible rotating labels and `aria-busy`. Focus
  rings, reduced-motion behaviour, dialog semantics, accessible names and the
  fixed semantic status colours (red error, green success, amber warning, blue
  info) are preserved. The motion is custom CSS/React inspired by
  `motion.dev/ui/buttons`, with no new dependency and no generic AI-looking
  form template.
- **Current-state role model (supersedes the older delegated-role wording in
  this report):** the built-ins are `SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`,
  `LEARNER` and `GUARDIAN`. `SUPER_ADMIN` is globally unrestricted, including
  institution management and granting any role; `ADMIN` is unrestricted within
  its own institution, can create/assign custom roles, and cannot grant
  `SUPER_ADMIN` or create global institutions. `CUSTOM` is a named reusable role
  with picked capabilities from the documented allowlist. It enters `/admin`
  only with `admin.access`; the backend enforces all other capabilities.
  `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER` are
  retired and existing accounts are migrated to `ADMIN`; `SUPER_ADMIN` is
  unchanged. **The migration changes only role values — no password is changed,
  generated or printed.** Custom-role CRUD is at `/api/auth/roles/`,
  `/api/auth/users/roles/` returns built-ins plus custom options, user payloads
  use `{ "role": "CUSTOM", "custom_role": <id> }`, and responses include
  `custom_role`, `custom_role_name` and `capabilities`.

**This is not production-ready.** Deployment/runtime verification remains:
proxy headers, TLS, media-serving permissions, least-privilege DB, shared
cache for throttles, SMTP, `manage.py check --deploy` with final values and
assistive-technology review. Reduced-motion browser checks have passed.

## 1. What was delivered

A working, integrated education platform combining an LMS, a Student
Information System and a digital publishing library. It is a modular monolith:
20 Django apps behind one REST API, consumed by one React web app, backed by
PostgreSQL `lms`.

| Deliverable | Where | State |
|---|---|---|
| Research report + Word document | repo root (`Kenyan_Digital_Learning_Ecosystem_Strategy_Report.*`) | Complete |
| Django backend + 20 apps | `backend/` | Complete |
| PostgreSQL schema + migrations | `backend/apps/*/migrations/` | Applied to `lms` |
| React 19 + Vite 8 frontend | `frontend/` | Complete, web-only |
| Public homepage and role-based auth | `frontend/src/pages/Home.jsx`, `Login.jsx`, `Register.jsx`, `AdminSignup.jsx`, `frontend/src/components/ParticleHeadline.jsx`, `frontend/public/images/`, `docs/ASSET_CREDITS.md` | Complete; photographed hero/workspaces, original insights section, accessible canvas headline, interactive role access preview, sparse links, admin portal not advertised publicly |
| Editable public content | `backend/apps/theming/site_content.py`, `frontend/src/config/publicSite.js`, `frontend/src/context/SiteContentContext.jsx`, `frontend/src/pages/AppearanceManager.jsx`, `frontend/src/pages/SiteContentManager.jsx`, `frontend/src/styles/sectionStyles.js`, `docs/PUBLIC_SITE_CONTENT.md` | `SUPER_ADMIN` and `ADMIN` edit palette, shared photos, wording and safe section styles from one `/admin/appearance` page; a custom role needs `admin.access` plus `appearance.manage`. Legacy aliases open the matching tab. Live API read; no offline cache |
| Public library books and resources | `backend/apps/content/views.py`, `backend/apps/content/serializers.py`, `backend/apps/content/migrations/0003_public_library_thumbnails.py`, `frontend/src/components/PublicBookShelf.jsx`, `frontend/src/components/ResourceCard.jsx`, `frontend/src/pages/Library.jsx` | Published, non-expired book metadata with local covers appears beside filtered resources with local thumbnails; licence-gated access stays in the portal |
| *(Removed)* PWA manifest + generated service worker | formerly `frontend/public/`, `frontend/dist/sw.js` | Removed; historical only |
| *(Removed)* Offline mutation queue | formerly `frontend/src/services/offlineQueue.js` | Removed; failed writes show an error and remain unsaved |
| Demo data command | `backend/apps/core/management/commands/seed_demo.py` | Complete |
| Backup / restore / environment scripts | `scripts/` | Complete; dumps under `backups/` are Git-ignored |
| Central reference-number generator | `backend/apps/core/codes.py` | Complete, tested |
| Production settings | `backend/config/settings_prod.py` | Fail-closed; requires `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins. Not a deployment sign-off |
| Two UI sides | `frontend/src/App.jsx`, `RoleHome.jsx`, `DashboardLayout.jsx`, `PortalLayout.jsx` | Implemented and browser-verified for staff, learner and guardian routes |
| School self-service profile | `backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`, `frontend/src/pages/SchoolProfile.jsx` | Migration applied after backup; API and focused tests passed |
| Documentation set | `docs/` | Written/updated; `SECURITY_AUDIT.md` documents hardening |
| Automated tests | `backend/apps/*/tests/`, `frontend/src/**/*.test.js` | Frontend **101 across 32 files**; focused backend security/auth/core/tutor/KEMIS suite **71 passing**; full backend suite **221 passed** |
| Invitation-only admin signup | `backend/apps/accounts/`, `frontend/src/pages/AdminSignup.jsx` | Single-use expiring server-side token; no public admin registration |
| Backend-enforced RBAC and scoped reads | `backend/apps/core/permissions.py`, `backend/apps/core/viewsets.py`, `frontend/src/components/ManagedResourcePage.jsx` | Write mixins, scoped reads and matching UI action flags; role/capability checks and self-escalation tests pass; `admin.access` gates admin-portal entry for custom roles |
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
| 6 — Parent & administration | Mostly implemented | Guardian links, scoped reports, announcements, messages; the portal has its own layout |
| 7 — Offline & mobile | **Removed by product direction change** | Earlier PWA shell, network-first API cache, offline banner and IndexedDB write queue were built, then deleted. There is no sync page, rebase/conflict UI or native wrapper |
| 8 — Advanced features | Partial | Reference numbering, charts and dashboard links plus a fee ledger, internal KICD-style review workflow, local KEMIS staging, bounded deterministic tutor and analytics/remediation rules are in place. Scale notifications, official KICD submission, official KEMIS transmission, LTI marketplace and optional hosted AI are not implemented |
| 9 — Production & handover | Not complete | Docs, tests and production settings exist, but no public deployment, load test, third-party security review or final runtime verification |

Do not describe Phases 7–9 as finished. Phases 0–6 are mostly implemented,
not a claim of 100% completion.

The separate product-direction phases in `docs/DEVELOPMENT_ROADMAP.md` use new
numbering: Phase 0 (direction and audit) is complete, Phase 1 (identity,
registration and onboarding) is complete, and Phase 2 (learner-centric resource
library) is complete with the caveats recorded in that roadmap. Existing phases
3–9 there are future work. Its old Phase 7 offline scope is superseded by
removal.

### Two UI sides and school profile

- `/` is a public homepage with a locally hosted hero photograph, three
  photographed workspace cards, an original progress/insights section and an
  interactive role selector with three previews: learners,
  guardians and teachers. The retired Content managers preview is removed from
  defaults and saved data. The hero headline is drawn by
  `ParticleHeadline.jsx` with a real `<h1>` for assistive technology, reduced
  motion support, pointer/touch repulsion, responsive resize and cleanup.
  The homepage does not advertise the internal administration portal. Public
  registration offers learner, guardian and teacher accounts only. Header,
  footer, homepage, role, library, sign in and portal wording are managed as one
  document at `/admin/appearance` (Words tab), read live from the API with local
  defaults. `ADMIN` and `SUPER_ADMIN` can edit wording; a custom role needs
  `admin.access` and `appearance.manage`. Managed photographs are on the Photos tab: each has a preview and
  upload, restore and remove actions, with validated JPG, PNG or WebP uploads
  published immediately. The Styles tab applies allowlisted colours, corners and
  spacing to one public section at a time; see `docs/PUBLIC_SITE_CONTENT.md`.
- `/library` is a public catalogue with real OER metadata and locally generated
  book covers and resource thumbnails. Images are responsive, lazy-loaded where
  below the fold, have meaningful alternative text where they convey content and
  fall back to typographic artwork if a file is missing. Repeated action labels
  were replaced with unique visible and accessible names. No unsafe third-party
  hotlinking is used; see `docs/ASSET_CREDITS.md`.
- Ocean Blue Serenity was the original default active palette; that is historical.
  Colours are data, not component literals. `apps.theming` stores the catalogue
  and active selection; `ThemeProvider` injects `--ramp-*` variables at runtime.
  **Current status (25 November 2026):** eight built-in palettes are seeded —
  Ocean Blue Serenity, Sage Green, Blue Coral Daylight, Forest Green, Citrus
  Bloom, Heritage Spice, Bright Horizon and Plum Harvest. Plum Harvest
  (`plum-harvest`, from `color 7.png`) is the active palette and the fresh-install
  default after the local `theming.0004_seed_and_activate_plum_harvest` migration.
  `SUPER_ADMIN` and `ADMIN` can manage palettes; a custom role needs
  `appearance.manage`; learners, guardians and teachers cannot. See
  `docs/DESIGN_SYSTEM.md`; `docs/OCEAN_PALETTE.md` records the earlier approval.
- Staff pages are at `/admin/...` with `DashboardLayout`; learner and guardian
  pages are at `/portal/...` with `PortalLayout`. Sign-in routes by role and
  `RoleHome` redirects old root URLs such as `/learners`, `/courses` and
  `/reports` to the right side. `/admin/login` and invitation-only
  `/admin/signup` remain the dedicated administrator entry points.
- School administrators can read and edit only their own school through
  `GET/PATCH /api/institutions/mine/` at `/admin/school`. Learners and
  guardians may read school details but get HTTP 403 on PATCH.
- `Institution` has `phone`, `email`, `website`, `motto` and `logo`. Logo
  uploads are multipart JPG/PNG/WebP, at most 2 MB, sniffed by magic bytes on
  the server, and need a live connection. `GET /api/auth/me/` returns
  `institution_logo`, which both layouts display with `/mark.svg` as fallback.
- Migration
  `backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
  was applied after the backup `backups/lms_20261123_134452.sql`.
- Admin list pages now share search, row-size, refresh and pagination controls
  through `useTableControls.js` and `TableTools.jsx`. Role filters remain on the
  user page; all controls are client-side over institution-scoped API results.

## 3. Verification actually performed

### Current web-only/security round — 24 November 2026

| Check | Result |
|---|---|
| Frontend `npx vitest run` | **98 passed across 32 files** |
| Frontend `npm run build` | Success; only `index.html`, hashed CSS/JS, `robots.txt`, SVG marks and local images. **No PWA, service-worker, workbox or manifest files** |
| `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Focused backend auth/account/core/tutor/KEMIS/security suite | Passing (**71 tests**) |
| Full backend suite | **221 passed, 107 subtests passed**; no failures or errors; system check clean |
| Django checks | No issues; `makemigrations --check --dry-run` reported `No changes detected` |
| Production `check --deploy` | Passed with placeholder production values; final values still to be checked |
| Git history / secrets | No credentials in source control; local `.env` secrets rotated; `backups/` ignored |
| Browser checks | Static desktop/390 px homepage, live `/login` auth animation, session login to `/portal`, and 390 px `/register` animation passed; no `klb_token`/`klb_user` in `localStorage`; forced reduced-motion browser checks passed at desktop and 390 px |

Assistive-technology review is still required; the reduced-motion path is
covered by the focused `ParticleHeadline` test and forced-media browser checks.
**Not production-ready**: see section 6 and `SECURITY_AUDIT.md`.

### Historical verification round — 24 November 2026 (theme manager)

The table below is retained for traceability. Its build and test numbers were
true at the time but have been superseded by the current round above; PWA
precache entries no longer exist. Role names in historical rounds reflect the
older model; retired names are now mapped to `ADMIN` as described in section 0.

| Check | Result |
|---|---|
| Frontend `npm test -- --run` | **93 passed across 32 files** |
| Frontend `npm run build` | Success; Vite reported one chunk over 500 kB (warning only); PWA generated **7** precache entries |
| Backend `manage.py check` | Clean, no issues |
| Backend `makemigrations --check --dry-run` | No changes detected |
| Backend `python -m pytest -q` | **134 passed** |
| Focused content and theming tests | **19 passed** |
| Migrations | Backups before `theming.0001_initial` and `content.0002_resource_taxonomy`, both applied locally |
| Production `check --deploy` | No issues at that time |
| `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Browser sweeps | Desktop and 390 px checks passed with no console errors or horizontal overflow; the admin shell had no idle offline panel |

That round used short-lived, server-generated API tokens for browser checks;
current authentication uses session cookies. It did not include a physical
device, destructive form submissions, logo upload, a fresh offline replay
(feature since removed) or assistive-technology testing.

### Earlier verification round — 23 November 2026

Historical results only. Notable superseded items: `npm run build` produced a
service worker with 6 precache entries; a browser check queued and replayed a
failed POST; Capacitor `mobile:sync` was reported. None of those paths exists
now.

## 4. Demo accounts

Run `python manage.py seed_demo` from `backend/` once if data is missing.

| Username | Role |
|---|---|
| `demo_admin` | `ADMIN` (institution administrator) |
| `demo_teacher` | `TEACHER` |
| `demo_learner` | `LEARNER` |
| `demo_guardian` | `GUARDIAN` |
| `platform_admin` | `SUPER_ADMIN` (demo username retained) |

Passwords are intentionally not reproduced, and no password is changed or
printed by the role migration. Set or reset one locally with
`python manage.py changepassword <username>` from `backend/`, or create a new
administrator with `python manage.py createsuperuser`. See `docs/ADMIN_ACCESS.md`.

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
Production configuration and the old service-worker kill-switch:
`docs/PRODUCTION_CONFIGURATION.md`.

## 6. Known limitations (must be disclosed)

1. **No offline or native support.** Failed writes show an error and stay
   unsaved; uploads need a live connection. Users of the old service worker
   need the manual deployment kill-switch or a site-data clear.
2. **No production deployment or final runtime verification.** Production
   settings exist and have passed `check --deploy` with placeholders, but no
   public server, load test, monitoring or third-party security review has been
   completed. Proxy headers, TLS, media permissions, least-privilege DB, shared
   throttle cache, SMTP and final deploy checks remain.
3. **Frontend test coverage is narrower than the full UI.** Utilities, guards,
   dashboards, reports, resource pages, public pages and auth are covered; not
   every CRUD dialog or destructive action has an automated test.
4. **Automated accessibility audit passed on the public homepage** (Lighthouse
   accessibility **1.00**, Best Practices **1.00**, SEO **1.00**) after darkening
   muted text and fixing metadata. An assistive-technology audit and human
   visual review are still outstanding, including the canvas hero.
5. **Generated textbook ISBNs are catalogue IDs**, not publisher-issued ISBNs.
   Supply the real ISBN when one exists.
6. Bounded modules remain bounded: fees are a school-office ledger with no
   gateway, KICD-style review is internal only, KEMIS export is local staging
   only, and the tutor is deterministic and curriculum-grounded unless an HTTP
   provider is explicitly configured.
7. Invitation tokens are high-entropy server-side tokens with expiry,
   single-use marking and revocation; they are stored in the database so an
   authorised admin can copy them later, and are **not** HMAC-signed or hashed.
   Treat the token like a credential.
8. Browser verification to date was DOM, layout-metric and console based.
   Screenshots were captured, but no human visual design review or
   assistive-technology audit was performed by this agent.
9. The project is not 100% complete: Phase 7 offline/native work was removed,
   Phase 8 is partial and Phase 9 is incomplete.

## 7. Security posture

- Passwords are stored with PBKDF2 hashing and validated; no password is in
  source, docs or sample data. Local `.env` remains Git-ignored and owner-managed, `backups/`
  is Git-ignored because dumps contain hashes/PII, and no secret is in source
  control.
- Login uses an HttpOnly Django session cookie; the readable CSRF cookie is
  echoed as `X-CSRFToken`. Identity/roles are always re-read from
  `/api/auth/me/`; no `klb_token`/`klb_user` in `localStorage`. Legacy token
  auth is compatibility-only and revoked on logout/password change/reset.
- DB-backed login lockout and scoped DRF throttles cover abuse paths;
  `X-Forwarded-For` is trusted only from configured proxy IPs.
- Reset links expire in one hour and use hashed, single-use records; password
  change/reset invalidates sessions.
- Institution isolation is enforced in shared querysets and serializers,
  including scoped content/assessment/course/learner/fee/attendance reads.
- Uploads are validated by magic bytes; health errors are generic; security
  headers and a production CSP are configured.
- Production settings require a separate `PRODUCTION_SECRET_KEY`, SMTP host,
  allowed hosts and CORS origins, and fail closed otherwise.
- This is **not** a substitute for deployment verification or a professional
  security review. See `SECURITY_AUDIT.md`.

## 8. Recommended next steps

1. Complete the deployment/runtime checklist in
   `PRODUCTION_CONFIGURATION.md` and `SECURITY_AUDIT.md`, including the old
   service-worker kill-switch.
2. Complete assistive-technology review; reduced-motion browser checks have
   passed under forced media at desktop and 390 px.
3. Add end-to-end tests with Playwright, including real session login and CRUD
   submissions.
4. Consider hashing invitation tokens and showing them only once at issue time.
5. Take a backup (`scripts/backup_database.ps1`) before any further schema work.
6. Deploy behind a reverse proxy with TLS using `config.settings_prod`, then
   run load testing, monitoring and an independent security review.
7. Do not commit or push unless explicitly asked; GitHub Desktop sync is
   expected once the user approves the changes.

## 9. Documentation index

Start at `docs/README.md`. Key guides: `SYSTEM_OVERVIEW.md`,
`INSTALLATION_GUIDE.md`, `COMMANDS.md`, `PRODUCTION_CONFIGURATION.md`,
`SECURITY_AUDIT.md`, `REFERENCE_NUMBERING.md`, `REFERENCE_MODELS.md`,
`DATABASE_GUIDE.md`, `API_DOCUMENTATION.md`, `USER_GUIDE.md`, `ADMIN_GUIDE.md`,
`ADMIN_ACCESS.md`, `TROUBLESHOOTING.md`, `BACKUP_AND_RESTORE.md`,
`FILE_STRUCTURE_GUIDE.md`, `DESIGN_SYSTEM.md`, `TESTING_CHECKLIST.md`,
`MILESTONES_AJ.md` (historical), and `NATIVE_WRAPPER.md` (removal notice).
