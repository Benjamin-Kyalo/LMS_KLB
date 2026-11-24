# Milestone record A–J: integrated public site, portals and final verification

**Date:** 23 November 2026  
**Folder:** `C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms`  
**Status:** implemented and verified locally. **No commit or push has been done.** The project folder is still untracked inside the parent GitHub Desktop repository.

This is the consolidated report for the whole delivered application, with emphasis on the final bundle: the public Zeraki-inspired homepage, hidden internal administration entry point, role-based public authentication, shared data tools for admin lists, invitation-only administrator access, labelled sample data and the final automated/browser verification.

`https://www.zeraki.app/` was used only as a general UI/UX and information-hierarchy reference. No Zeraki logo, copy, images, layout assets or code were copied. The KLB palette, wording, routes and original SVG illustration remain distinctive to this project.

**Final observed results:** backend `manage.py check` clean; `makemigrations --check --dry-run` → `No changes detected`; backend `pytest -q` → **95 passed**; frontend `npm test -- --run` → **52 passed across 19 files**; `npm run build` succeeded with one non-fatal >500 kB chunk warning and **7** PWA precache entries; `npm audit --audit-level=moderate` → **0 vulnerabilities**; production `check --deploy` → no issues; sample seeder → all categories `[OK]`, **0** new records on the final rerun; 10 desktop/emulated-mobile CDP browser checks passed with no console errors or horizontal overflow. A later homepage refactor added local photographs, an original insights section and fewer repeated links; it was rechecked in-app at 1000×700 and with a credential-free CDP pass at 390×844 with 0 overflow, 0 admin links and no console errors.

---

## A. What

1. **One integrated platform.** React + Vite consumes one Django/DRF backend and one PostgreSQL `lms` database. There are no duplicated datasets for the public site, admin portal or learner/guardian portal.
2. **Public website at `/`.** A clean homepage with a locally hosted hero photograph, three photographed workspace cards, a facts strip, an original progress/insights section with a KLB SVG, an interactive role selector and a professional footer. Choosing a role reveals that role's rights and content. Repeated quick-access, workspace, section-anchor and footer authentication links were removed.
3. **Role-based public entry.** `/login` and `/register` support learner, guardian and teacher accounts with role-specific fields and validation. Administrator access is not advertised in public navigation or general registration.
4. **Dedicated administration portal.** `/admin`, `/admin/login` and invitation-only `/admin/signup` are the internal entry points. `/admin/...` provides management pages for people, structure, academics, courses, assessment, curriculum, publishing, communication and reports.
5. **Role-specific portal.** `/portal/...` gives learners and guardians their own navigation, home, courses, textbooks, resources, reports, messages and profile. Assignments and quizzes are learner-only.
6. **Backend-enforced RBAC and isolation.** Institution-scoped querysets, write mixins, role-hierarchy checks, self-escalation blocking and frontend action flags secure the same records on both sides.
7. **Administrator invitations.** Expiring, single-use, high-entropy server-side tokens are issued by authorised admins. Admin roles cannot be obtained through public registration.
8. **Labelled sample data.** An add-only idempotent seeder supplies more than 10 varied, realistic, fictional records per relevant category, with no passwords generated, printed or stored.
9. **Admin data tools.** Shared search, row-size selection, refresh and pagination were added to resource lists and the custom Users, Learners and Admin Invitations pages.
10. **Responsive verification.** Layouts were checked at 1440×900 and emulated 390×844, including mobile menus, cross-side redirects and role-gated navigation. The refactored homepage was rechecked at 1000×700 and 390×844 with all images loaded and no overflow.

## B. Why

- The user asked for one centralised platform, not separate public and admin systems or static mockups.
- The homepage should guide visitors to the right role without overwhelming them or exposing internal administration.
- Zeraki demonstrates a professional education-site rhythm: strong hero, clear product areas, facts and visible progress. The project needed that hierarchy without copying its identity, and duplicate role links were deliberately avoided.
- Ordinary signup must not grant administrator privileges; administrator creation needs an authorised, auditable path.
- Students, parents, teachers and admins need different views of the same underlying records, with permissions enforced on the server.
- Development and testing need believable, internally consistent data that is unmistakably fictional.
- Dense admin tables need usable search and pagination, and all pages must remain usable on small screens.

## C. How

- **Shared architecture:** Django apps expose one REST API; DRF serializers and viewsets own validation, scoping and permissions; React services call that API through `frontend/src/services/api.js`.
- **Public/home:** `Home.jsx` renders original copy, four locally hosted Unsplash photographs and a local `/hero-learning.svg`. Four role buttons drive an access preview with rights and content lists and one workspace link for the selected role; one generic `/register` and one generic `/login` link are also rendered. No `/admin` link, no “Quick access” block and no repeated section anchors are rendered. Footer content and role previews come from `frontend/src/config/publicSite.js`.
- **Auth:** TokenAuthentication and SessionAuthentication; custom `accounts.User` with `role` and `institution`. Login and registration redirect by role. Admin creation is gated by `AdminInvitation`.
- **Integration:** admin-created learners, teachers, guardians and academic records are ordinary API records; portal pages query the same endpoints with tighter scoping. Deactivation and deletion therefore apply everywhere.
- **RBAC:** `InstitutionScopedQuerysetMixin` scopes lists and forces `institution` on writes; `can_assign_role()` prevents role escalation; `AdminWriteMixin`, `StaffWriteMixin`, `PlatformWriteMixin` and `ContentWriteMixin` enforce write permissions. `ManagedResourcePage` derives UI action flags from endpoint scope and fails closed for unknown endpoints.
- **Codes:** `apps/core/codes.py` generates references with PostgreSQL advisory locks. Official supplied codes are preserved when unique.
- **Data tools:** `useTableControls.js` holds query/page/page-size state; `TableTools.jsx` renders the toolbar and pagination; list components pass institution-scoped rows into them.
- **Offline:** service worker, cached reads, network-first API reads and an IndexedDB mutation queue exist. Logo upload deliberately requires a live connection. A stale write is rebased once against the server's current version; unresolved conflicts keep the local details for manual retry/discard.
- **Sample data:** the seeder checks and creates labelled records add-only. Its output reports every category and enforces a minimum of 10.

## D. Files and their responsibilities

| Area | File(s) | Responsibility |
|---|---|---|
| Public site | `frontend/src/pages/Home.jsx`, `frontend/src/pages/Home.test.jsx` | Original KLB homepage; sparse auth links, photographed workspaces, facts, insights, interactive role access preview; tests assert no admin link, no repeated auth links, no public sample-data notice and no removed taglines |
| Public content config | `frontend/src/config/publicSite.js`, `docs/PUBLIC_SITE_CONTENT.md` | Editable footer and role rights/content previews with optional runtime override |
| Original artwork | `frontend/public/hero-learning.svg` | Locally authored illustration of books, profiles and charts used in the insights section |
| Photography | `frontend/public/images/*.jpg`, `docs/ASSET_CREDITS.md` | Four locally hosted Unsplash photos with source URLs and licence reference |
| Public auth | `frontend/src/pages/Login.jsx`, `Register.jsx`, `AdminSignup.jsx`, `Login.test.jsx`, `Register.test.jsx`, `AdminSignup.test.jsx` | Role-aware sign-in/registration; teacher approval notice; invitation redemption; tests keep admin access out of public navigation |
| Routing/guards | `frontend/src/App.jsx`, `components/RoleHome.jsx`, `ProtectedRoute.jsx`, `ProtectedRoute.test.jsx`, `RoleHome.test.jsx`, `utilities/roles.js` | Public routes, `/admin`, `/portal`, legacy redirects, role sets and hierarchy helpers |
| Layouts | `frontend/src/layouts/DashboardLayout.jsx`, `PortalLayout.jsx` | Distinct staff/portal navigation, school identity, mobile menu toggles |
| Styling | `frontend/src/styles/tokens.css`, `global.css` | Exact required palette, shared cards/tables/nav rhythm, responsive and small-screen rules |
| Admin lists | `frontend/src/components/ResourcePage.jsx`, `ManagedResourcePage.jsx`, `hooks/useTableControls.js`, `components/TableTools.jsx`, related tests | CRUD modals, endpoint-derived permissions, search/page-size/refresh/pagination |
| Custom admin pages | `frontend/src/pages/Users.jsx`, `Learners.jsx`, `AdminInvitations.jsx` | Specialised management pages with the same data tools and their own filters |
| Dashboards/reports | `frontend/src/pages/Dashboard.jsx`, `Reports.jsx`, `components/ChartCard.jsx` | Recharts visuals, scoped figures, clickable dashboard actions |
| Portal pages | `frontend/src/pages/PortalHome.jsx`, `PortalCourses.jsx`, `PortalAssignments.jsx`, `PortalQuizzes.jsx`, `PortalCommunications.jsx`, `PortalResources.jsx`, `components/PortalList.jsx` | Learner/guardian views over shared API records |
| API client/offline | `frontend/src/services/api.js`, `offlineQueue.js`, `registerSW.js` | One HTTP boundary, pagination fix, mutation queue, PWA registration |
| Auth backend | `backend/apps/accounts/{models,serializers,views,urls}.py` | User model, public registration, invitations, login/profile/password endpoints |
| Permissions | `backend/apps/core/{permissions,viewsets,codes}.py` | Role hierarchy, write mixins, institution scoping, reference numbers |
| Sample data | `backend/apps/core/management/commands/seed_sample_data.py`, `docs/SAMPLE_DATA.md` | Add-only labelled seeder and its category/count documentation |
| Migrations/backups | `backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`, `backups/lms_20261123_143556.sql` etc. | Applied schema changes with database backups taken first; no schema change in the final UI round |
| Production config | `backend/config/settings_prod.py`, `.env.example`, `scripts/` | Deploy checks, secret template, backup/restore helpers |
| Docs | `docs/*.md`, root `README.md` | Operating manuals, honest phase status, testing record and this A–J report |

## E. Implementation summary

- The public homepage has six purposeful sections: a sparse topbar, hero photograph, three photographed workspaces, four facts, an original progress/insights panel, an interactive role selector and a professional footer. Selecting a role reveals its rights and content from `publicSite.js`. The three static taglines and the public sample-data notice were removed at the user's request; sample records remain labelled inside the authenticated applications. Repeated feature lists and duplicate links were avoided.
- Public registration exposes only `LEARNER`, `GUARDIAN` and `TEACHER`. Required fields change with the role. Teacher accounts start inactive pending school approval.
- The internal admin portal is reachable at its prescribed `/admin` route. `/admin/login` and `/admin/signup` exist, but neither appears on the public homepage, in the role selector or its preview, in registration fields or in standard `/login`/`/register` navigation.
- Admin and portal shells use the same palette and section rhythm but different density. Active navigation now uses a clear forest fill with an ochre rule; cards have strong top rules; tables have tinted headers and compact rows. Ochre remains decorative; readable amber text uses `--amber-text`.
- Admin lists share table controls. `ResourcePage` covers the many standard resources; Users, Learners and Invitations use the same hook/components with their own filters.
- Backend rules remain authoritative. Hiding a button never substitutes for a serializer/permission check. Self-deletion and self role escalation are blocked.
- The admin invitation token is stored server-side so authorised administrators can copy it later. It is high-entropy, expiring, single-use and revocable, but **not** HMAC-signed or hashed; treat it as a credential.
- Database credentials remain in a Git-ignored `.env`; `.env.example` is the template. No password was generated, printed, stored or invented by this work.

## F. Run commands (with directory)

Backend — working directory `...\kenyan-lms\backend`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe manage.py seed_sample_data
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Frontend — working directory `...\kenyan-lms\frontend`:

```powershell
npm test -- --run
npm run build
npm audit --audit-level=moderate
npm run dev
```

Production settings check — working directory `...\kenyan-lms\backend`, with explicit hosts/CORS/CSRF values supplied for the check:

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings_prod"
$env:ALLOWED_HOSTS="127.0.0.1,localhost,lms.example.test"
$env:CORS_ALLOWED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"
$env:CSRF_TRUSTED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"
.\.venv\Scripts\python.exe manage.py check --deploy
```

Full command reference: `docs/COMMANDS.md`. Backup before any future schema work with `scripts/backup_database.ps1`.

## G. Test steps and observed results

1. `manage.py check` → **System check identified no issues**.
2. `makemigrations --check --dry-run` → **No changes detected**.
3. `python -m pytest -q` → **95 passed**.
4. `npm test -- --run` → **52 passed across 19 files**.
5. `npm run build` → success; 2619 modules transformed; one >500 kB chunk warning; PWA precache **7 entries**.
6. `npm audit --audit-level=moderate` → **found 0 vulnerabilities**.
7. `check --deploy` with `config.settings_prod` → **no issues**.
8. `seed_sample_data` → **0 new records**; every listed category `[OK]`.
9. `GET /api/health/` → HTTP 200, `{"status":"ok","service":"KLB Digital Learning Ecosystem","database":"connected","error":null}`; `GET http://127.0.0.1:5173/` → HTTP 200.
10. CDP browser harness at **1440×900** and **390×844** → all 10 checks passed:
    - desktop and mobile homepage: hero, illustration, three workspaces, facts, four role cards, 0 overflow;
    - public `/login` and `/register`: 0 `/admin` links; `/admin/login` still rendered the dedicated form;
    - admin dashboard: shells, KPI cards and charts rendered; mobile menu opens;
    - `/admin/users`: search, filter, row-size, refresh and pagination controls present; search changed visible rows;
    - learner portal: desktop shell and cards rendered;
    - guardian portal: mobile menu works, Assignments hidden, direct `/portal/assignments` redirects to `/portal`;
    - cross-side redirects: learner at `/admin` → `/portal`, admin at `/portal` → `/admin`;
    - console: no errors in any check.
11. Earlier checks in the final round covered `/home`, legacy `/dashboard`, all 34 admin routes, platform-only redirects, report charts and the 12-row exam table. Two real defects were found and fixed: stale `ResourcePage` imports after the `ManagedResourcePage` rename, and absolute DRF `next` URLs being double-prefixed by `listAll`.
12. After the final homepage refactor, an in-app Chromium check at **1000×700** and a credential-free CDP check at **390×844** confirmed: four headings, all five images loaded, three single-column workspace cards on mobile, single-column insights on mobile, **0** horizontal overflow, **0** `/admin` links, **1** `/login` link, **1** `/register` link, **3** unique section anchors, no “Quick access” text and no console errors.
13. After the role-selector/footer-config change, an in-app Chromium check confirmed the default learner preview, and clicking “Parents & guardians” switched `aria-pressed`, the rights/content lists and the workspace link to `/login?role=GUARDIAN`. A credential-free CDP check at **390×844** then showed single-column selector, preview and detail grids, all five images loaded, and a “Teachers” click switching the link to `/login?role=TEACHER`. The three removed taglines and the sample notice were absent, footer values came from `publicSite.js`, and there were **0** admin links, **1** `/login`, **1** `/register`, **3** unique anchors, **0** overflow and no console errors. Lighthouse then scored the public homepage **1.00** for accessibility, best practices and SEO after contrast, meta-description and robots.txt fixes.

14. A final module sweep at **390×844** rendered admin fees, approval, KEMIS, tutor, analytics and sync, plus portal home, fees, remediation, tutor and sync: **0** horizontal overflow and **0** console errors. Role gates redirected a learner from `/admin` to `/portal` and a guardian from `/portal/remediation` to `/portal`. Public `/`, `/login` and `/register` each had **0** `/admin` links. Three real defects found during this sweep were fixed and rechecked: paginated tutor messages, duplicate React keys in cohort tables, and the portal report chart's exam-label field.

The first CDP harness used short-lived, server-issued API tokens for existing demo accounts. No password was typed, printed or stored. Temporary token, harness, result log and screenshot files were removed after capture. The second harness used no credentials; its script and browser profile were also deleted. The final module harness used short-lived server-issued tokens again; its loader, token files, script, browser profile and verification tab were all removed afterwards.

## H. Expected result and what was actually observed

- **Expected:** a polished public entry point, internal admin portal, role-specific portal, shared records, enforced permissions, labelled data and responsive pages.
- **Observed:** all of the above are implemented locally. The public homepage contains no admin navigation, no repeated quick-access block and only one generic registration/sign-in link each; admin and portal records come from the same API; role gates and institution scoping are enforced in code and tested; all automated and selected browser checks passed.
- **Automated audit:** Lighthouse on the public homepage scored accessibility **1.00**, best practices **1.00** and SEO **1.00** after contrast, meta-description and robots.txt fixes.
- **Not claimed:** a physical-device audit, human visual design review of the captured screenshots, destructive CRUD browser replay after the last UI change, logo-upload replay, fresh offline mutation replay, deployment, load testing, third-party security review, accessibility audit with assistive technology, or completion of Phases 7–9.

## I. Common errors and fixes

| Symptom | Likely cause | Check / fix |
|---|---|---|
| Public homepage shows an admin link | Old cached bundle or stale service worker | Hard refresh; unregister service worker; `Home.test.jsx` asserts 0 `/admin` links |
| Learner visiting `/admin` is redirected | Correct role gate | Use `/portal`; inspect `/api/auth/me/` role |
| Admin visiting `/portal` is redirected | Correct role gate | Use `/admin` |
| Teacher cannot sign in after registering | Teacher accounts start inactive by design | A school administrator must approve the account |
| Administrator signup is rejected | Public registration has no admin role | Use an invitation issued at `/admin/invitations` and redeem at `/admin/signup` |
| Cross-school detail returns 404 | Institution scoping is working | Do not try to bypass with a client-side `institution` value |
| Table shows no rows after search | Search term does not match displayed fields | Clear the search box or refresh |
| Pagination buttons are absent | Only one page or no filtered rows | Expected; the control hides when `totalPages <= 1` |
| Logo upload fails offline | Uploads deliberately bypass the JSON queue | Reconnect and retry |
| `makemigrations --check` reports changes | Model changed without a migration | Back up, review and generate a migration before applying |
| Vite warns about a large chunk | Bundle-size advisory | Not a failure; consider code splitting later |

## J. Documentation and honest status

- New/rewritten: `docs/MILESTONES_AJ.md`, `docs/SAMPLE_DATA.md`, `docs/ADMIN_ACCESS.md`, `docs/COMMANDS.md`, `docs/REFERENCE_MODELS.md`, `docs/ASSET_CREDITS.md`, `docs/PUBLIC_SITE_CONTENT.md`.
- Updated with final counts, invitation/RBAC details, public homepage behaviour and API endpoints: root `README.md`, `docs/README.md`, `docs/TESTING_CHECKLIST.md`, `docs/HANDOVER_REPORT.md`, `docs/IMPLEMENTATION_CHECKLIST.md`, `docs/API_DOCUMENTATION.md`, `docs/ADMIN_GUIDE.md`, `docs/USER_GUIDE.md`, `docs/SYSTEM_OVERVIEW.md`, `docs/DESIGN_SYSTEM.md`.
- Related background: `docs/DATABASE_GUIDE.md`, `docs/BACKUP_AND_RESTORE.md`, `docs/PRODUCTION_CONFIGURATION.md`, `docs/TROUBLESHOOTING.md`, `docs/FILE_STRUCTURE_GUIDE.md`, `docs/REFERENCE_NUMBERING.md`.
- Status wording to preserve everywhere: **Phase 0–6 mostly implemented; Phase 7 foundation only; Phase 8 partial; Phase 9 incomplete. This project is not 100% complete.**
- No commit or push was performed. GitHub Desktop sync remains for the user to approve.
