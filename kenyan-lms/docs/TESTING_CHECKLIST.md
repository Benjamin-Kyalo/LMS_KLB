# Testing checklist

## Second homepage enhancement set, 27 November 2026

| Check | Command / method | Result |
|---|---|---|
| Homepage regression | `npm test -- --run src/pages/Home.test.jsx` | **7 tests passed**; covers the skip link, reading indicator, dismissible announcement, quick links, readiness checklist, routines, access table, usability notes, support callout and back-to-top behaviour |
| Final frontend suite | `npm test -- --run --maxWorkers=2` | **51 files / 175 tests passed**. The default fully parallel run hit a few 5s timeouts while the backend suite was competing for CPU; the two-worker rerun passed cleanly |
| Production build | `npm run build` | Passed; no service worker, PWA manifest or workbox files |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Backend theming checks | `$env:DB_NAME="lms_extra_homepage_check"; python manage.py test apps.theming --verbosity 1 --noinput` | **22 tests OK**; new copy, safe-link validation and section styles covered |
| Migration and system checks | `python manage.py migrate theming`, `python manage.py check`, `python manage.py makemigrations --check --dry-run` | `theming.0008_add_public_homepage_extras` applied; system check clean; `No changes detected` |
| Live browser audit | Accessibility snapshot and console on `http://127.0.0.1:5173/` | Announcement, quick links, routines, access table, checklist, usability notes, support callout, skip link, reading indicator and back-to-top all render; 0 unnamed links and 0 console errors |
| Lighthouse | In-app Chromium on `/` | Accessibility **1**, Best Practices **1**, SEO **1**, 0 failures after the support heading contrast fix |
| Whitespace check | `git diff --check` | No whitespace errors; only the existing CRLF normalization warnings |

The second set adds no images, dependencies, animation libraries, service
workers, raw CSS fields or retired cards. All edits remain uncommitted.

## Public homepage revamp, 27 November 2026

| Check | Command / method | Result |
|---|---|---|
| Homepage and managed-content regression | `npm test -- --run src/pages/Home.test.jsx src/config/publicSite.test.js src/pages/SiteContentManager.test.jsx src/pages/AppearanceManager.test.jsx` | **21 tests passed**; covers the new guided sections, labelled menu disclosure, Escape close, safe internal/external links, retired-card rejection and Appearance editing |
| Final frontend suite | `npm test -- --run` | **51 files / 174 tests passed** |
| Production build | `npm run build` | Passed; no service worker, PWA manifest or workbox files |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Backend theming checks | `python manage.py test apps.theming.tests.test_theming` | Passed; public defaults and managed photo slots remain valid |
| Final full backend suite | `$env:DB_NAME="lms_homepage_check"; python manage.py test --verbosity 1 --noinput` | **283 tests OK** in `808.100s`; system check clean |
| Migration check | `python manage.py migrate theming`, then `python manage.py check` and `python manage.py makemigrations --check --dry-run` | `theming.0007_refresh_public_homepage` applied; system check clean; `No changes detected` |
| Live browser audit | Accessibility snapshot, console errors and Lighthouse on `http://127.0.0.1:5173/` | New hero, trust strip, guide, spotlight, role selector and questions render from the managed document; no unnamed links and no blocking console errors; Lighthouse accessibility, best practices and SEO all scored **1** |
| Whitespace check | `git diff --check` | Clean apart from existing CRLF normalization warnings |

The managed migration replaces only known old header, hero and caption values
and fills missing fields; administrator photos, credits and other custom wording
are preserved. No new dependency, animation library, service worker, raw CSS
field or retired card was introduced.

## Feature round — rubrics, mastery, low bandwidth, interop and governed AI, 26 November 2026

| Check | Command / method | Result |
|---|---|---|
| Rubric backend | Focused rubric Django tests | **10 tests OK** |
| Frontend suite before the last three features | `npm test -- --run` | **47 files / 161 tests passed** |
| Final frontend suite | `npm test -- --run` | **51 files / 172 tests passed** |
| Full backend suite after rubrics | `DB_NAME=lms_full_check python manage.py test --verbosity 1` | **268 tests OK** in `9733.255s`; historical feature checkpoint |
| Full backend suite before the homepage revamp | `DB_NAME=lms_final_check2 python manage.py test --verbosity 1` | **283 tests OK** in `1043.618s`; includes rubrics, mastery, low bandwidth, OneRoster and governed AI; system check clean |
| Frontend production build | `npm run build` | Passed; `dist` has no service worker, manifest or workbox files; existing chunk-size warning remains |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Mastery backend | `python manage.py test apps.analytics.tests.test_mastery` | **4 tests OK**; bands, staff/learner scoping, filters and derived-only behaviour covered |
| Mastery frontend | `npm test -- --run src/pages/MasteryBadges.test.jsx` | **3 tests OK**; staff and learner screens render derived badges without award rows |
| Low-bandwidth frontend | `npm test -- --run src/services/lowBandwidth.test.js src/services/api.test.js src/pages/LowBandwidth.test.jsx src/pages/MasteryBadges.test.jsx` | **16 tests OK** after path normalisation and cell-role fixes |
| Low-bandwidth backend | `python manage.py test apps.core.tests.test_low_bandwidth apps.theming` | **25 tests OK**; public config, allowlists, sensitive-body rejection and stale-write 409s covered |
| Tutor, OneRoster and low-bandwidth backend | `$env:DB_NAME="lms_focus_check"; python manage.py test apps.tutor apps.integration apps.core.tests.test_low_bandwidth` | **23 tests OK**; policy payload, `tutor.answer.requested`/`generated` audit redaction, HS256 assertions, scope/institution pinning, explicit protocol rejection and conflict checks covered |
| Governed tutor frontend | `npm test -- --run src/pages/TutorWorkspace.test.jsx` | **1 test OK**; policy version and plain-language data exclusions render |
| Django check | `python manage.py check` | No issues |
| Migration drift | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| Whitespace check | `git diff --check` | Clean (only existing CRLF normalization warnings) |

No browser-level offline replay, physical-device test, assisted-technology
review, live SIS exchange or external AI call was performed. The
low-bandwidth mode is off by default; see `OFFLINE_MODE_REVERSAL.md`. Client
secrets and integration credentials were never printed.

## Current verification — library and appearance round, 25 November 2026

| Check | Command / method | Result |
|---|---|---|
| Frontend suite | `npx vitest run --testTimeout=20000` from `frontend/` | **101 tests across 32 files** |
| Library and photo checks | `npx vitest run src/components/ResourceCatalogue.test.jsx src/pages/SiteContentManager.test.jsx src/pages/AppearanceManager.test.jsx src/pages/ThemeManager.test.jsx src/services/api.test.js` | Passed; cover/thumbnail fallbacks, unique action names, photo CRUD, client-side dimension blocking, field-level API error messages, unified Appearance tabs and school-admin photo access are covered |
| Full backend suite | `python -m pytest --durations=5` from `backend/` | **221 passed, 107 subtests passed** in 65.15s; no failures or errors. `backend/conftest.py` uses a test-only fast password hasher; the PBKDF2 assertion explicitly overrides it |
| Focused backend photo/library suite | `python -m pytest apps/theming/tests apps/content/tests` | **44 passed**; artwork serialization, photo remove/reset endpoints and school-admin photo permissions are covered |
| Library migration/data | `python manage.py migrate content`, then a Django shell check | `content.0003_public_library_thumbnails` applied; public books use verified OER titles and local covers, public resources use curated links and local thumbnails |
| Shared photo migration/data | `python manage.py migrate theming`, then a Django shell check | `theming.0005_set_shared_hero_photo` applied; stored and public `hero.imageSrc` both resolve to `/images/hero-community.png` |
| Active palette/data | Django shell check after final verification | Eight built-ins remain; Plum Harvest (`plum-harvest`) is the single active palette, matching the fresh-install default |
| Frontend production build | `npm run build` from `frontend/` | Success; `dist` contains `hero-community.png` and no service worker, PWA manifest, workbox or precache files. The existing main JS chunk-size warning remains non-blocking |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Django checks | `python manage.py check`, `python manage.py makemigrations --check --dry-run` | No issues; `No changes detected` |
| Photo upload 400 reproduction | Django APIClient with a `success.jpg` (1200×1200) and a `skill 2.jpg` (236×314) against `/api/theming/site-content/image/`, rolled back after the request | Valid file returned `201`; the undersized file returned `400` with `image: Use a photo at least 640×360 pixels.`. The Photos card now blocks that file before the request and shows the reason inline |
| Button interaction sweep | Full frontend suite plus a source grep for plain action labels | Common visible action labels use `RollingLabel`; destructive actions use `HoldToConfirmButton`; busy labels stay plain; accessible names, focus rings, reduced motion and dialog semantics are preserved |

Deployment/runtime and assistive-technology checks are still required. The
project is **not production-ready**; see `SECURITY_AUDIT.md`.

**Current-state note — role-model simplification:** the built-ins are
`SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER` and `GUARDIAN`. Retired
`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER`
accounts migrate to `ADMIN`; `SUPER_ADMIN` is unchanged and no password is
changed or printed. Custom roles pick from the documented capability allowlist,
enter `/admin` only with `admin.access`, and are enforced by the backend. API
coverage to add for this model: `/api/auth/roles/` CRUD, role options from
`/api/auth/users/roles/`, `{role:"CUSTOM", custom_role:<id>}` payloads, response
fields (`custom_role`, `custom_role_name`, `capabilities`), the
`SUPER_ADMIN`-only grant/institution boundary, and capability denial. The
historical rows below still use earlier role names and result counts; they are
retained for traceability, not presented as current test totals.

## Historical — web-only security round, 24 November 2026

| Check | Command / method | Result |
|---|---|---|
| Frontend suite | `npm test` from `frontend/` | **97 tests across 32 files** |
| Frontend production build | `npm run build` from `frontend/` | Success. Output contains only `index.html`, hashed CSS/JS assets, `robots.txt`, SVG marks and local images; **no service worker, PWA manifest, workbox or precache files** |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Focused backend suite | auth/account/core/tutor/KEMIS/security tests | Passing (**71 tests**) |
| Full backend suite | `DJANGO_SETTINGS_MODULE=config.settings python manage.py test apps` | **215 passed in 862.901s**; `OK`; system check clean |
| Django checks | `manage.py check`, `makemigrations --check --dry-run` | No issues; `No changes detected` |
| Production deploy check | `manage.py check --deploy` | Passed with placeholder production values; final values pending |
| Git/secrets | history and `.env` review | No credentials in source control; local `.env` secrets rotated; `backups/` Git-ignored (hashes/PII) |
| Auth animation / session browser pass | In-app Chromium against rebuilt preview and Django | `/login` and `/register` text visible before/during/after click; pressed class clears; live login succeeds; `/portal` loads under session cookie; no `klb_token`/`klb_user` in `localStorage`; 390 px form has no overflow |
| `ParticleHeadline` reduced motion | Focused Vitest component test plus in-app Chromium harness forcing `matchMedia` and reduced-motion CSS | Passed: no animation frames or canvas context in the unit test; in the browser at desktop and 390 px the real `<h1>` stayed visible with opacity `1`, the canvas stayed `display: none`, `requestAnimationFrame` was never called, and the accessibility tree exposed the heading. Assistive-technology review still pending |

Proxy-header, TLS, media-permission, shared-cache, SMTP and assistive-technology
checks are still required. Static and forced-reduced-motion browser checks
already confirmed the canvas hero's real `<h1>`, one `aria-hidden` canvas and no
horizontal overflow at desktop and 390 px. The project is **not
production-ready**. See `SECURITY_AUDIT.md`.

**Supersession notice:** every round below is historical. PWA precache entries,
service-worker builds, offline queue replay, sync pages/banners, Capacitor
config and `npm run mobile:sync` were later **removed** by the web-only product
direction change. They are retained for traceability only and are **not**
current capabilities or claims. A one-release `/sw.js` kill-switch (or site-data
clear) remains a manual deployment step for previously installed clients.

## Historical — Public library and quiet status polish — 24 November 2026

| Check | Command / method | Result |
|---|---|---|
| Focused backend tests | `python -m pytest apps/content/tests/test_resources.py apps/theming/tests/test_theming.py -q` | **19 passed** |
| Full backend suite | `python -m pytest -q` | **134 passed** |
| Full frontend suite | `npm test -- --run` from `frontend/` | **93 passed across 32 files**; the previously hanging site content manager test was fixed by stabilising its content effect |
| Frontend production build | `npm run build` from `frontend/` | Success; **7** PWA precache entries; one existing Vite chunk >500 kB warning |
| Dependency audit | `npm audit --audit-level=moderate` from `frontend/` | **0 vulnerabilities** |
| Django checks | `python manage.py check`, `python manage.py makemigrations --check --dry-run` | No issues; no changes detected |
| Live API | `GET /api/content/public/books/`, `GET /api/theming/site-content/` | **13** published books; role cards `learners, guardians, teachers` |
| Desktop browser check | In-app Chromium at 1000 px | `/library` showed 13 book cards and the resource catalogue; `/` had only three role previews and **0** `/admin` links; `/admin` had no idle offline panel; **0 console errors**, **0 horizontal overflow** |
| 390 px browser check | Temporary same-origin 390×844 harness | `/library` and `/admin` rendered with **0 horizontal overflow**; no retired Content managers preview and no idle offline panel; harness file and tab removed |

At that historical point the PWA write queue and dedicated sync page still
existed; only the always-visible, empty “Offline changes / 0 pending /
0 conflicts” block had been removed from the shells. **Both the queue and sync
page were removed later.** Today a failed mutation shows an error and remains
unsaved by default; the separate narrow, env-driven mode documented in
`OFFLINE_MODE_REVERSAL.md` is not that old queue.

## Historical — Phase 1 + Phase 2 closeout — 24 November 2026

| Check | Command / method | Result |
|---|---|---|
| Pre-migration backup | `scripts\backup_database.ps1` | `backups\lms_20261124_105943.sql` written before the Phase 2 structural migration |
| Applied migration | `python manage.py migrate` | `content.0002_resource_taxonomy` applied locally |
| Focused content tests | `python -m pytest apps/content/tests -q` | **9 passed** |
| Full backend suite | `python -m pytest -q` | **133 passed** |
| Django system check | `python manage.py check` | No issues |
| Migration drift | `python manage.py makemigrations --check --dry-run` | No changes detected |
| Frontend unit/component tests | `npm test -- --run` from `frontend/` | **82 passed across 28 files**; a transient timeout while the backend suite ran concurrently cleared on an isolated rerun |
| Frontend production build | `npm run build` from `frontend/` | Success; **7** PWA precache entries; one existing Vite chunk >500 kB warning |
| Dependency audit | `npm audit --audit-level=moderate` from `frontend/` | **0 vulnerabilities** |
| Live API | `GET /api/health/`, `/api/content/facets/`, `/api/content/public/resources/`, `/api/content/collections/`, `/api/content/embed-providers/` | HTTP 200 with valid JSON after restarting the dev server against current code |
| Desktop browser sweep | In-app Chromium, 1000 px wide, server-issued tokens | `/`, `/library`, `/register`, `/login`, learner `/portal`, `/portal/resources`, guardian `/portal/documents`, teacher `/admin`, school-admin `/admin/theme`, `/admin/teacher-approvals`, `/admin/guardian-links`, platform `/admin/resources`, `/admin/resource-collections`, `/admin/embed-providers` all rendered the expected heading; **0 horizontal overflow**, **0 console errors** |
| 390 px browser sweep | Same-origin temporary 390×844 iframe harness | All 14 routes above rendered the expected heading; **0 horizontal overflow**, **0 console errors**; public pages had **0** `/admin` links |
| Temporary harness cleanup | File deletion and tab close | `frontend/public/mobile-check.html` and both temporary browser tabs removed |

Not claimed in this round: fresh browser-level offline replay, physical-device
testing, signed native build, deployment/load test, third-party security review,
assistive-technology audit, official KICD/KEMIS submission, or human visual
design review. Local uploads, private media serving in production, large video
hosting and external embeds beyond the active allowlist remain explicit
operational decisions. No commit or push was made.

## Earlier verification round — 23 November 2026 (final consolidated pass)

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
| Public homepage, desktop and mobile | Rendered the hero, original SVG illustration, three workspaces, facts strip and four role cards (the facts strip was removed later); **0 horizontal overflow**, **0 admin links**, no console errors |
| Public homepage after the photo/insights refactor | In-app Chromium at 1000×700 and a temporary CDP check at 390×844: hero photo, three workspace photos, original insights SVG, four role cards rendered and the later-removed facts strip still present; **0 horizontal overflow**, **0 admin links**, **1** `/login` link, **1** `/register` link, **0** “Quick access” links, **3** unique section anchors; all five images loaded; no console errors |
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

## Final palette-change round — 24 November 2026

After the approved Ocean Blue Serenity palette was applied:

| Check | Command / method | Result |
|---|---|---|
| Frontend unit tests | `npm test -- --run` | **52 passed across 19 files** |
| Production build | `npm run build` | Successful; **7** PWA precache entries |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Capacitor sync | `npm run mobile:sync` | Build plus `cap sync` succeeded for Android and iOS projects |
| Backend tests | `python -m pytest -q` | **95 passed** |
| Django system check | `python manage.py check` | No issues |
| Browser palette check | In-app Chromium on `/` | Body/card backgrounds `rgb(255,255,255)`; hero/footer `rgb(2,62,138)`; computed colours limited to the extracted blue ramp plus transparent/root defaults; **0** horizontal overflow, **0** `/admin` links, no console errors |
| Browser auth/public routes | In-app Chromium on `/login`, `/register`, `/admin/login`, `/portal` | White backgrounds; `/login`, `/register` and redirected `/portal` had **0** `/admin` links; **0** horizontal overflow; no console errors |
| Lighthouse after palette | In-app Chromium on `/` | Accessibility **1.00**, Best Practices **1.00**, SEO **1.00**; no failures |

The offline queue tests in `frontend/src/services/conflictResolution.test.js`
and `offlineQueue.test.js` were included in the 52 passing frontend tests. A
fresh browser-level offline replay, physical-device test and human visual design
review were not repeated in this round; the palette change did not alter layout
structure. See `docs/OCEAN_PALETTE.md` for the exact colour values and semantic
decision.

## Theme manager round — 24 November 2026

| Check | Command / method | Result |
|---|---|---|
| Pre-migration backup | `scripts\backup_database.ps1` | `backups\lms_20261124_101534.sql` written before applying the structural migration |
| Migration | `python manage.py migrate` | `theming.0001_initial` applied; Ocean Blue Serenity active, Sage Green available |
| Backend tests | `python -m pytest -q` | **100 passed** |
| Frontend unit tests | `npm test -- --run` | **62 passed across 22 files** |
| Production build | `npm run build` | Successful; **7** PWA precache entries |
| Dependency audit | `npm audit --audit-level=moderate` | **0 vulnerabilities** |
| Django system check | `python manage.py check` | No issues |
| Browser theme route | In-app Chromium signed in as `demo_admin` | `Theme & colours` visible in admin navigation; `/admin/theme` loads catalogue, active palette and onboarding form; no console errors |
| Access rules | Backend/frontend tests | School, institution and platform admins can manage palettes, shared photos, wording and section styles; learners/guardians/teachers receive HTTP 403 or a UI denial |

The verification did not activate a different palette: Ocean Blue Serenity remains
the active selection. Runtime palette helpers, CSS injection, contrast feedback
and school-admin access have automated coverage.

**Later palette addition (25 November 2026):** `theming.0003_seed_swatch_palettes`
adds Blue Coral Daylight, Forest Green, Citrus Bloom, Heritage Spice and Bright
Horizon. It is idempotent and leaves the active palette untouched. The focused
theming suite passes **15 tests**; every new ramp passes the same WCAG text
contrast validator used by the admin form. `makemigrations --check --dry-run`
reports no changes.

**Current palette status (25 November 2026):** the historical rounds above left
Ocean Blue Serenity active. The local `theming.0004_seed_and_activate_plum_harvest`
migration has since been applied: eight built-in palettes are seeded, including
Plum Harvest (`plum-harvest`, from `color 7.png`), and Plum Harvest is verified
active and is the fresh-install default. Full re-verification is being run
separately; the recorded result numbers above are unchanged.

## Earlier results — 23 November 2026

| Check | Command | Result |
|---|---|---|
| Django system check | `python manage.py check` | No issues |
| Migrations applied | `python manage.py migrate` | All apps OK |
| Backend test suite | `python -m pytest` | **28 passed, 52 subtests passed** |
| Frontend unit tests | `npm test` | **8 passed** (3 files) |
| Frontend production build | `npm run build` | Success; PWA service worker generated |
| Health endpoint | `GET /api/health/` | `status: ok`, `database: connected` |
| Login | `POST /api/auth/login/` | Historical legacy token auth: token returned, `role: SCHOOL_ADMIN`. Login now sets a session cookie instead |
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
  cannot create users, role list (built-ins plus custom options from
  `/api/auth/users/roles/`).
- **Institution isolation** — `ADMIN` sees only its own institution;
  `SUPER_ADMIN` sees all; `ADMIN` cannot create global institutions.
- **Learners** — account + profile created together, cross-school invisibility,
  duplicate admission number rejected.
- **Courses** — cross-school list/detail blocked, progress marking idempotent.
- **Assessment** — correct answer earns marks, wrong answer earns zero.
- **Helpers** — date formatting, role identification.
- **Endpoint smoke** — every list endpoint returns < 500 for an institution
  administrator (`ADMIN`).
- **Reference codes** — generated admission/staff/course codes, per-school
  sequences, institution abbreviations and API creation without a code.
- **School profile** — `GET/PATCH /api/institutions/mine/` is limited to the caller's
  own school; `ADMIN` can update phone/email/website/motto; a valid PNG
  logo is accepted, a text file is rejected; learners get HTTP 403 on PATCH;
  `GET /api/auth/me/` includes `institution_logo`.
- **Two sides** — `RoleHome` and `ProtectedRoute` unit tests cover role-based
  redirects and guards for `/admin` and `/portal`.
- **Production config** — `check --deploy` with `config.settings_prod`.

## Rubric round — 26 November 2026 (actually executed)

- Backend focused suites `apps.courses.tests.test_rubrics` and
  `apps.curriculum.tests.test_rubrics`: **10 tests passed**. Coverage includes
  criterion validation, institution and rubric-set checks, direct-score grading,
  publication notifications, guardian academic permission, resubmission limits,
  audit institution scoping, percentage-band validation and the feedback bank.
- Frontend full suite (`npm test`): **47 files, 161 tests passed**, including new
  rubric builder, teacher grading/publication and learner/guardian submission
  tests.
- `npm run build`: passed; rubric pages remain lazy-loaded chunks and no new
  runtime dependency was added.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `git diff --check`: no whitespace errors; CRLF conversion warnings only.

## Current limitations (honest, web-only product)

- No native-device testing was performed. The 390×844 checks used browser
  emulation, and there is no native app to test: the Capacitor wrapper was
  removed (`docs/NATIVE_WRAPPER.md`).
- Destructive CRUD submissions and logo upload were not replayed in the last
  browser round; the underlying API and earlier browser replay are covered by
  tests and previous notes.
- No automated end-to-end login test with a real password for the current
  session-cookie flow; historical portal checks used short-lived server-generated
  tokens. Current auth uses the HttpOnly session cookie and `X-CSRFToken`.
- No offline/queue testing applies: the mutation queue, sync/conflict UI and
  service worker were removed. Failed writes show an error and stay unsaved;
  browser and assistive-technology checks now cover that path instead.
- Official KICD submission and KEMIS transmission/template validation are not
  implemented; the workflows are internal/local only.
- Hosted AI provider configuration and load testing are outstanding; the tutor
  is local and deterministic by default.
- Deployment, runtime verification, load testing and monitoring are incomplete
  (Phase 9). Proxy headers, TLS, media permissions, least-privilege DB, a shared
  throttle cache, SMTP and final `check --deploy` still need verification.
- Third-party security review is outstanding (see `SECURITY_AUDIT.md`).
- Accessibility audit with assistive technology is outstanding (WCAG 2.2 AA is
  guidance, not a completed audit). The canvas hero's real `<h1>` and
  reduced-motion fallback must be included.

## Rule

A test is only "passed" when it has actually been run and its output is
recorded here. Do not mark pending items as done.
