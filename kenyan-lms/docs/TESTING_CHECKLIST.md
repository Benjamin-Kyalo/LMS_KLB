# Testing checklist

## Latest verification round — 23 November 2026 (final consolidated pass)

| Check | Command / action | Result |
|---|---|---|
| Frontend unit/component tests | `npm test -- --run` from `frontend/` | **52 passed across 19 files** |
| Frontend production build | `npm run build` from `frontend/` | Success; one Vite chunk >500 kB warning (not a failure); PWA generated **7** precache entries |
| Django system check | `python manage.py check` from `backend/` | Clean, no issues |
| Migration drift | `python manage.py makemigrations --check --dry-run` from `backend/` | No changes detected |
| Full backend suite | `python -m pytest -q` from `backend/` | **95 passed** |
| Production settings | `DJANGO_SETTINGS_MODULE=config.settings_prod python manage.py check --deploy` | No issues, with explicit `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` values |
| npm advisories | `npm audit --audit-level=moderate` from `frontend/` | **0 vulnerabilities** |
| Sample seeder | `python manage.py seed_sample_data` | All categories `[OK]`; **0** new records on the final rerun |
| Live API health | `GET http://127.0.0.1:8000/api/health/` | HTTP 200; `status: ok`, `database: connected` |
| Live UI | `GET http://127.0.0.1:5173/` | HTTP 200 |
| Extended module browser sweep | In-app Chromium plus a temporary CDP harness at **390×844** | Admin fees, approval, KEMIS, tutor, analytics and sync, plus portal home, fees, remediation, tutor and sync all rendered; **0 horizontal overflow**, **0 console errors** |
| Role gates and public navigation | Browser DOM checks | Learner `/admin` → `/portal`; guardian `/portal/remediation` → `/portal`; public `/`, `/login` and `/register` each had **0** `/admin` links |
| Native wrapper config | `npx cap ls` and `docs/NATIVE_WRAPPER.md` | Capacitor config parsed with pinned 8.6.2 packages; no device build or store artefact |

### Desktop and emulated-mobile browser verification

A temporary Chrome DevTools Protocol harness opened the real Vite app at
**1440×900** and **390×844** viewports. Authentication used short-lived,
server-issued API tokens for existing demo accounts; no password was typed,
printed or stored. The temporary token file and harness were deleted afterwards.
A second, credential-free CDP check at **390×844** was used after the homepage
photo/insights refactor; its script and browser profile were also deleted.

| Check | Result |
|---|---|
| Public homepage, desktop and mobile | Rendered the hero, original SVG illustration, three workspaces, facts strip and four role cards; **0 horizontal overflow**, **0 admin links**, no console errors |
| Public homepage after the photo/insights refactor | In-app Chromium at 1000×700 and a temporary CDP check at 390×844: hero photo, three workspace photos, original insights SVG, facts strip and four role cards rendered; **0 horizontal overflow**, **0 admin links**, **1** `/login` link, **1** `/register` link, **0** “Quick access” links, **3** unique section anchors; all five images loaded; no console errors |
| Public homepage after role-selector/footer-config change | In-app Chromium plus a credential-free CDP check at **390×844**: four role buttons, selected role's rights/content and one matching workspace link; clicking “Parents & guardians” in-app switched the preview/link to `/login?role=GUARDIAN`, and clicking “Teachers” at 390×844 switched to `/login?role=TEACHER`; selector, preview and detail columns all single-column on mobile; all three removed taglines and the sample notice absent; footer renders `publicSite.js` values; all five images loaded; **0 admin links**, **1** `/login`, **1** `/register`, **3** unique anchors, **0 overflow**, no console errors |
| Lighthouse on public homepage | Accessibility **1.00**, Best Practices **1.00**, SEO **1.00**. Contrast, meta description and robots.txt issues found in the first run were fixed by darkening `--ink-faint`, adding a meta description and adding `frontend/public/robots.txt` |
| Public registration, mobile | Role-based form rendered at 390 px with no horizontal overflow |
| Public auth pages | `/login` and `/register` contained **0** `/admin` links; `/admin/login` still rendered the dedicated administrator sign-in form |
| Admin dashboard, desktop and mobile | Sidebar, KPI cards and charts rendered; no horizontal overflow |
| Mobile admin menu | Toggle visible; sidebar hidden initially, visible and `.is-open` after tapping |
| Admin list tools | `/admin/users` rendered search, role filter, row-size control, refresh and pagination; typing a search term reduced the visible rows |
| Learner portal, desktop | Portal shell, navigation and cards rendered; no horizontal overflow |
| Guardian portal, mobile | Menu toggle works; Assignments link hidden; direct `/portal/assignments` redirected to `/portal`; no horizontal overflow |
| Cross-side role gates | Learner visiting `/admin` redirected to `/portal`; admin visiting `/portal` redirected to `/admin` |
| Console | No console errors in any of the above checks |

The extended module sweep used short-lived, server-issued API tokens for existing demo
accounts; no password was typed, printed or stored. The temporary loader, token files,
CDP script, browser profile and verification tab were deleted afterwards. It found three
real defects, all fixed and rechecked: the tutor workspace assumed a bare array where the
API returns a paginated message object; the analytics cohort table produced duplicate
React keys; and the portal home chart assumed an `exam` field where the report API returns
`label`. The fixed pages re-rendered with no console errors and no overflow at 390×844.

Earlier browser checks in this round also covered public `/home`, `/login`,
`/admin/login`, `/admin/signup`, legacy `/dashboard`, all 34 admin routes,
platform-only route redirects, report charts and the 12-row exam table.
Two real defects found and fixed were stale `ResourcePage` imports after the
`ManagedResourcePage` rename, and an absolute DRF `next` pagination URL being
double-prefixed by `listAll`.

Screenshots were captured for the public, admin and portal views. The checks
above were DOM, layout-metric and console based; a human visual design review
was not performed by this agent.

An automated Lighthouse audit of the public homepage now passes accessibility,
best practices and SEO at **1.00** each. Still not covered by browser replay or
external review in this final round: destructive CRUD submissions, school-logo
upload, assistive-technology testing, physical-device testing and a fresh
offline mutation replay. Those remain limitations, not claimed passes.

## Earlier results — 23 November 2026

| Check | Command | Result |
|---|---|---|
| Django system check | `python manage.py check` | No issues |
| Migrations applied | `python manage.py migrate` | All apps OK |
| Backend test suite | `python -m pytest` | **28 passed, 52 subtests passed** |
| Frontend unit tests | `npm test` | **8 passed** (3 files) |
| Frontend production build | `npm run build` | Success; PWA service worker generated |
| Health endpoint | `GET /api/health/` | `status: ok`, `database: connected` |
| Login | `POST /api/auth/login/` | Token returned, `role: SCHOOL_ADMIN` |
| Learner list | `GET /api/learners/` | `count: 1` (demo admin) |
| Dashboard | `GET /api/reports/dashboard/` | 1 learner, 5 attendance records, 80% attendance |
| Frontend dev server | `GET http://127.0.0.1:5173/` | HTTP 200, manifest served |
| Migration drift | `python manage.py makemigrations --check --dry-run` | No changes detected |
| Browser: login flow | Fill the locally reset `demo_admin` credentials, submit | Redirected to dashboard; `/api/auth/login/` 200 |
| Browser: dashboard | Inspect rendered DOM | Nav + user name + dashboard stats rendered; `/api/reports/dashboard/` 200 |
| Browser: learners list (old root URL, before the `/admin` split) | Navigate to `/learners` (now redirects to `/admin/learners` for staff) | Table shows `Amina Otieno · ADM001 · Grade 4 · ACTIVE` |
| Browser: create learner | Open modal, submit `ADM002` | `POST /api/learners/` 201; table refreshed to 2 rows |
| Browser: textbooks (old root URL) | Navigate to `/textbooks` (now `/admin/textbooks` or `/portal/textbooks` by role) | Published KLB demo title with chapter count rendered |
| Browser: learner report (old root URL) | Select `Amina Otieno` in `/reports` (now `/admin/reports` or `/portal/reports`) | Attendance 4 PRESENT / 1 LATE; exam 78.00 B; average 78 |
| Browser console | Collect console messages | No errors (only React DevTools info message) |
| Frontend unit tests (after offline work) | `npm test` | **8 passed** (3 files) |
| Frontend build (after offline work) | `npm run build` | Success; PWA service worker generated |
| Browser: offline queue | Simulate failed POST in browser | "1 change waiting to sync"; table unchanged |
| Browser: queue replay | Restore network, click Sync now | "1 change(s) sent"; table refreshed to 3 rows |

## Actually executed — 23 November 2026 (hardening round)

| Check | Command / action | Result |
|---|---|---|
| Django check | `python manage.py check` | No issues |
| Migration drift | `python manage.py makemigrations --check --dry-run` | No changes detected |
| Backend suite | `python -m pytest` | **28 passed, 52 subtests passed** |
| Production settings | `DJANGO_SETTINGS_MODULE=config.settings_prod python manage.py check --deploy` | No issues |
| Email deprecation | Full pytest after migrating to `MAILERS` | No `EMAIL_BACKEND` warning |
| Frontend tests | `npm test` (Vitest 4.1.12) | **8 passed** |
| Frontend build | `npm run build` | Success; 6 PWA precache entries |
| npm advisories | `npm audit --audit-level=moderate` after pinned upgrades/overrides | **0 vulnerabilities** |
| Nested content API | GET modules, lessons, questions, chapters, resources | All returned 200 after router fix |
| Browser: nested pages (old root URLs) | Open `/modules`, `/lessons`, `/questions`, `/chapters`, `/resources` (now under `/admin/...`) | All rendered; no console errors |
| API: auto admission number | POST learner without `admission_number` | `ADM-DEMO01-001` returned |
| Browser: auto admission number | Register learner with admission field blank | Table showed `ADM-DEMO01-002`; form accepted blank |
| Reference-number tests | `python -m pytest apps/core/tests/test_reference_codes.py` | **6 passed** |

## Backend tests by purpose

- **Authentication** — login success/failure, protected profile, teacher
  cannot create users, role list.
- **Institution isolation** — school admin sees only own institution;
  platform admin sees all; school admin cannot create institutions.
- **Learners** — account + profile created together, cross-school invisibility,
  duplicate admission number rejected.
- **Courses** — cross-school list/detail blocked, progress marking idempotent.
- **Assessment** — correct answer earns marks, wrong answer earns zero.
- **Helpers** — date formatting, role identification.
- **Endpoint smoke** — every list endpoint returns < 500 for a school admin.
- **Reference codes** — generated admission/staff/course codes, per-school
  sequences, institution abbreviations and API creation without a code.
- **School profile** — `GET/PATCH /api/institutions/mine/` is limited to the caller's
  own school; school admins can update phone/email/website/motto; a valid PNG
  logo is accepted, a text file is rejected; learners get HTTP 403 on PATCH;
  `GET /api/auth/me/` includes `institution_logo`.
- **Two sides** — `RoleHome` and `ProtectedRoute` unit tests cover role-based
  redirects and guards for `/admin` and `/portal`.
- **Production config** — `check --deploy` with `config.settings_prod`.

## Pending (honest limitations)

- Native-device testing: the final pass used Chrome's 390×844 emulation, not a
  physical phone or tablet.
- Destructive CRUD submissions and logo upload were not replayed in this final
  browser round; the underlying API and earlier browser replay are covered by
  tests and previous notes.
- Automated end-to-end login test with a real password; the final portal check
  used short-lived server-generated API tokens instead.
- Fresh offline mutation and forced-conflict replay on a physical device; unit
  tests cover the first-pass rebase and manual fallback, but no device replay
  was performed.
- Signed native APK/IPA and store submission; only Capacitor wrapper scaffolding
  exists (`docs/NATIVE_WRAPPER.md`).
- Official KICD submission and KEMIS transmission/template validation; the
  implemented workflows are internal/local only.
- Hosted AI provider configuration and load testing; the tutor is local and
  deterministic by default.
- Deployment, load testing and monitoring (Phase 9 — not complete).
- Third-party security review.
- Accessibility audit with assistive technology (WCAG 2.2 AA is guidance,
  not a completed audit).

## Rule

A test is only "passed" when it has actually been run and its output is
recorded here. Do not mark pending items as done.
