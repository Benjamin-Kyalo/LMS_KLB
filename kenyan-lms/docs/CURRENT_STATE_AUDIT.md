# Current-state audit — 24 November 2026

Status: **Completed as a read-only baseline**. No application code was changed and
no tests were re-run during this audit pass. Test counts below were the latest
recorded **at audit time**; see `docs/TESTING_CHECKLIST.md` for current figures.

Purpose: establish what already works before any new module is added, so the new
product direction improves the existing platform instead of rebuilding it.

**Supersession notice:** this was a point-in-time baseline. Later on 24 November
2026 the product direction changed to a **normal web app only**. Every
PWA/offline/native item below is historical: the IndexedDB mutation queue,
sync/conflict pages and banners, service worker, PWA manifest, workbox
precache, Capacitor config and `frontend/android` / `frontend/ios` were removed.
Failed mutations now show an error and remain unsaved; uploads need a live
connection. The homepage hero now has an accessible canvas particle headline
with a real `<h1>`. Authentication is session-cookie based with CSRF and
`/api/auth/me/` identity reads. See `README.md` and `SECURITY_AUDIT.md`.

**Role-model supersession notice:** the audit-time role descriptions below are
retained as dated history. Current built-ins are `SUPER_ADMIN` (global
unrestricted, institution management and any role grant), `ADMIN` (unrestricted
in its own institution, can create/assign custom roles, cannot grant
`SUPER_ADMIN` or create global institutions), `CUSTOM`, `TEACHER`, `LEARNER` and
`GUARDIAN`. `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and
`CONTENT_MANAGER` are retired and those accounts migrate to `ADMIN`; passwords
are never changed or printed. Custom roles carry picked capabilities, enter
`/admin` only with `admin.access`, and are managed at `/api/auth/roles/`. See
`USER_ROLES_JOURNEYS.md`.

## Executive summary

This is already a substantial, working modular monolith. It has a public site,
a restricted staff/admin side, a learner/guardian portal, a shared DRF API,
PostgreSQL `lms`, role and institution scoping, and a runtime theme catalogue.
It should be **extended, not replaced**. The PWA/offline foundations noted in
the original audit have since been removed.

The remaining gaps are concentrated in product-facing completeness rather than
core architecture:

- registration exists but is a single conditional form, not role-specific
  onboarding with first-run checklists;
- teacher approval exists as generic user activation, not a dedicated approval
  workflow with class assignment;
- guardian–learner linking exists in the API but has no frontend management
  screen or verified registration link;
- learning resources exist and support files, but the admin form excludes
  upload UX and portal lists are flat/unfiltered;
- public content is partly config-driven, but there is no admin-managed page,
  navigation, media library or dashboard configuration;
- the shared staff dashboard is not yet four distinct role dashboards;
- *(historical)* offline conflict handling was first-pass only and was never
  replayed on a physical device or in a fresh browser-level session; the whole
  offline feature was subsequently removed;
- production media serving, deployment, monitoring and external security review
  remain out of scope;
- several docs contained stale app/test counts and two different phase numbering
  schemes. The main counts were reconciled in this Phase 0 pass.

## What exists and should be preserved

| Area | Existing evidence | Preserve / extend |
|---|---|---|
| Stack and shape | React 19 + Vite 8, Django 6.1 + DRF 3.18, PostgreSQL `lms`, 20 local Django apps in `backend/config/settings.py` | Keep the modular monolith and one SPA. Auth is now Django session cookies with CSRF (legacy token auth only for compatibility) |
| Three experiences | Public `/`, staff `/admin/*` using `DashboardLayout`, portal `/portal/*` using `PortalLayout`; role-safe redirects in `frontend/src/App.jsx` | Keep the route split; do not add admin links to public pages |
| Identity and access | `accounts.User` with six built-in role kinds (`SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER`, `GUARDIAN`) plus named custom roles; public registration limited to `LEARNER`, `TEACHER`, `GUARDIAN`; expiring single-use `AdminInvitation`; inactive teachers on registration | Extend into role-specific forms, onboarding and a dedicated approval view |
| RBAC and isolation | Capability checks, permission classes, `InstitutionScopedQuerysetMixin`, forced institution on writes, backend tests; custom roles enforce every picked capability and need `admin.access` for `/admin` | Keep backend-authoritative checks; mirror only for UI affordances |
| School records | Institution, department, year, term, class, subject, learner, teacher assignment, guardian link, transfer models and CRUD screens | Reuse as the source of truth for Phase 3 membership work |
| Curriculum and publishing | CBE framework/levels/learning areas/strands/outcomes/rubrics; publishers, textbooks, chapters, resources, exercises and access records | Build the learner-facing resource discovery layer on these, not a parallel catalogue |
| Teaching and assessment | Courses, modules, lessons, progress, assignments, submissions, questions, quizzes, exams and results | Extend scoping and UI; avoid duplicating records |
| Attendance/reports/comms | Attendance records, report snapshots, announcements, notifications, messages, notification preferences | Use for role dashboards and guardian visibility |
| Bounded modules | Fees ledger, approval workflow, KEMIS staging, local/deterministic tutor, analytics snapshots/remediation | Keep the approved boundaries; do not turn them into payments, transmission or AI decisions |
| PWA/offline | **Historical:** `vite-plugin-pwa`, network-first API cache, IndexedDB mutation queue, auto-sync and conflict UI existed at audit time | **Removed.** Do not rebuild; failed mutations show an error and stay unsaved |
| Theming | `ThemePalette` catalogue, one active palette, public active endpoint, admin CRUD/activation, contrast validation, `ThemeProvider`, CSS variables, chart/meta derivation | Keep as the branding baseline; `ADMIN` and custom roles with `appearance.manage` have access. Homepage canvas hero must keep a real `<h1>` and reduced-motion support |
| Verification | **Historical at audit time:** backend 100 passed, frontend 62 across 22 files, build with 7 precache entries, audit 0 vulnerabilities, Django check clean | Current: frontend 101 across 32 files, full backend 221 passed, clean web-only build, audit 0 vulnerabilities; focused backend suite 71 passing; reduced-motion browser checks passed under forced media, assistive-technology review pending |

## Gap assessment against the new target

Priority follows `docs/FUNCTIONAL_REQUIREMENTS.md`; phase follows the new
`docs/DEVELOPMENT_ROADMAP.md`.

| Requirement | Current position | Gap | Priority | Phase |
|---|---|---|---|---|
| PUB-01 public homepage | Strong hero, role preview, registration/sign-in entry, no public admin links | Catalogue/document/announcement entry could be more prominent and admin-editable | P0 | 2, 5 |
| PUB-02 institutional information | KLB reference reviewed; project has public content but not a full managed institutional section | Move story/mandate/leadership/contact into managed records progressively | P1 | 5 |
| PUB-03 resource catalogue | Digital textbook/resource models and public catalogue exist | No level/subject/class/collection filter UI on public/portal lists; no unified public resource catalogue | P0 | 2 |
| PUB-04 documents/forms | Reference pattern understood; no generic document library model/UI | Add admin-managed documents with categories, previews and safe download | P1 | 2, 5 |
| PUB-05 announcements | Announcement model and admin page exist | Audience targeting exists in model but not in admin form; public/news presentation is thin | P1 | 5 |
| PUB-06 images/videos/documents | File/image fields exist; school logo upload is wired | Admin resource form excludes upload; no generic media library; external embeds undecided | P1 | 2, 5 |
| PUB-07 registration starting point | Public register page asks role and shows conditional fields | Not yet distinct multi-step Student/Teacher/Guardian onboarding | P0 | 1 |
| PUB-08 responsive/accessibility | Earlier Lighthouse 1.00 and 390px checks passed | Re-check after each new module; no assistive-technology audit yet | P0 | Every phase, 9 |
| PUB-09 SEO/metadata | Meta description, theme colour, robots.txt present | Must survive CMS migration | P1 | 5 |
| REG-01 learner fields | DOB/gender required in serializer; profiles created atomically | Confirm final minimum field set; add onboarding completion state | P0 | 1 |
| REG-02 teacher inactive until approval | Inactive account creation and activation endpoint exist | Dedicated approval/assignment workflow and onboarding checklist missing | P0 | 1 |
| REG-03 guardian linked to learner | `LearnerGuardian` model and API exist | No verified registration link, no admin/guardian UI to manage links | P0 | 1 |
| REG-04 no public admin registration | Public roles exclude admins; invitations are expiring/single-use | Preserve and test after registration changes | P0 | 1 |
| REG-05 role landing/onboarding | `homeFor()` sends staff to `/admin`, portal roles to `/portal` | First-run checklists and role-specific landing states not implemented | P0 | 1 |
| REG-06 profile maintenance | Users can maintain permitted profile fields | Confirm sensitive fields cannot be self-escalated after onboarding changes | P1 | 1 |
| ADM-01 global + institution admins | `SUPER_ADMIN` full global control; `ADMIN` full control in its own institution; custom roles capability-bound | Confirm the simplified model; keep invitation-only creation and self-escalation tests | P0 | 1 |
| ADM-02 CRUD/search/filter/pagination | Shared managed-resource pattern is in place | Apply consistently to new CMS/media/structure screens | P0 | 2–5 |
| ADM-03 people/accounts | Users, roles, invitations screens exist | Add pending teacher approvals and guardian link verification views | P0 | 1 |
| ADM-04 academic structure | Institution setup screens exist | Ensure full year/term/class/subject/enrolment/assignment chain is managed and scoped | P0 | 3 |
| ADM-05 learning resources | Resource/textbook CRUD exists | Add uploads, taxonomy, access scope and discoverability | P0 | 2 |
| ADM-06 pages/media/documents | Logo and theme are admin-managed | No page/section, generic media or document library UI | P1 | 5 |
| ADM-07 navigation editor | Static config and layout nav | No validated admin navigation model | P1 | 5 |
| ADM-08 dashboard config | No widget configuration | Decide which approved cards each role may toggle | P1 | 4 |
| ADM-09 announcements/notifications | Announcements and messages exist | Expose audience, category and publish scheduling in admin UI | P1 | 5 |
| ADM-10 branding/theme | Palette manager and logo upload implemented | Preserve; extend only if per-institution branding is approved | P0 | 8 |
| ADM-11 permissions/settings | Code-based permissions; no SystemSetting model | Keep code-based RBAC; add only safe validated settings records | P0 | 8 |
| ADM-12 reports/audit/health | Reports and bounded analytics exist | Audit browsing and health reporting could be consolidated; no sync/queue health (queue removed) | P1 | 4, 6 |
| ADM-13 validation/audits | Validation and audit patterns exist in sensitive modules | Ensure every new state change follows the same pattern | P0 | Every phase |
| TCH-01 teacher dashboard | Shared staff analytics dashboard with quick links | Build a teacher-specific “my classes/learners/work” view | P0 | 4 |
| TCH-02–03 resources/uploads | Teachers and staff with `content.manage` can manage content via API/UI patterns | Add scoped upload UX and validation | P0 | 2 |
| TCH-04–07 assessment/progress/comms | Models exist | Ensure workflows and scoping are coherent in role UI | P1 | 6 |
| LRN-01–03 learner dashboard/resources/work | Portal exists but lists are flat | Learner-specific dashboard and filtered resource/assignment views | P0 | 2, 4 |
| LRN-04–05 progress/profile | Reports and portal home exist | Plain-language progress and profile completion | P1 | 4, 6 |
| GRD-01–04 guardian portal | Portal home shows “No linked learner yet” | Verified linking, linked-learner scoping, targeted notices and readable reports | P0 | 1, 4, 6 |
| PLT-01 backend authority | RBAC/scoping tests exist | Keep proving 401/403 and isolation for every new endpoint | P0 | Every phase |
| PLT-02 shared records | Same API feeds all sides | Avoid new duplicate resource/catalogue models | P0 | Every phase |
| PLT-03 list contracts | DRF filters/pagination and `useList` exist | Apply to new modules | P0 | Every phase |
| PLT-04 states | Shared notices/empty-state patterns exist | Use them in every new screen | P1 | Every phase |
| PLT-06 responsive/accessibility | Prior desktop/390px checks passed | Re-verify per module | P0 | Every phase |
| PLT-07 web reliability (offline safety requirement removed) | Queue and conflict UI existed at audit time | **Removed:** failed writes show an error and remain unsaved; no queue, replay or conflict UI | P1 | 7 (superseded) |
| PLT-08 audit trail | Sensitive changes audited | Extend to new content/CMS changes | P1 | 5, 6 |
| PLT-09 sample data | Labelled sample seeder exists | Add labelled samples for new modules without invented passwords | P1 | Every phase |
| PLT-10 bounded integrations | Fees/KICD/KEMIS/tutor limits documented | Preserve boundaries | P1 | 9 |

## Concrete mismatches found in this pass

1. **App count was stale.** README and handover said 14 Django apps; settings
   and directory inventory show 20. Main docs were corrected.
2. **Test counts were stale.** Some docs reported 45/18 and 50 backend or 52/19
   and 95 backend. The latest recorded round is 62 frontend across 22 files and
   100 backend. Main docs now point to the latest round.
3. **Two phase numbering schemes exist.** Older delivery docs say Phases 0–6 are
   mostly implemented, 7 foundation, 8 partial, 9 incomplete. The new product
   roadmap reuses phase numbers for a different sequence. `docs/README.md` now
   warns readers not to mix them.
4. **Teacher approval is generic activation.** `POST /api/auth/users/{id}/set_active/`
   from the Users screen is not the same as approve + assign classes + onboarding.
5. **Guardian linking is API-only.** `/api/learners/guardian-links/` exists, but
   no frontend screen manages it and the portal asks guardians to contact admin.
6. **Upload UX is incomplete.** `ContentResource` supports a `FileField`, but the
   admin Resources form explicitly tells users to use the API.
7. **Portal resource discovery is flat.** `PortalCourses.jsx` and
   `PortalResources.jsx` do not expose subject/class/level filters.
8. **Admin customisation is bounded.** No page/section model, navigation editor,
   dashboard widget config or generic media library was found.
9. **Announcement targeting is not exposed.** `audience_roles` exists in the
   model but not in `Communications.jsx`.
10. **Production media serving is unresolved.** Django serves `/media/` only when
    `DEBUG`; no object storage or web-server media route is configured.
11. **Dashboards are shared, not role products.** `Dashboard.jsx` is one school
    analytics view for all staff, with role-conditional links and an admin panel.
12. **Offline and native were foundations at audit time.** They are now
    **removed** by the web-only product direction; no replay or native build is
    expected.
13. **External hardening was out of scope at audit time.** Security controls
    have since been added, but deployment/runtime verification, load testing,
    monitoring, third-party security review and assistive-technology checks are
    still outstanding (see `SECURITY_AUDIT.md`).
14. **Offline/native direction changed after this audit.** The options recorded
    above for hardening the queue and conflict UI were replaced by removal.

## Decisions now resolved

Confirmed by the user on 24 November 2026:

- one primary `SUPER_ADMIN` with complete control, plus delegated platform and
  school administrators created only through controlled invitations; *(historical
  decision, superseded by the simplified `SUPER_ADMIN`/`ADMIN`/`CUSTOM` model
  described at the top of this document)*;
- teacher accounts remain inactive until an administrator approves them;
- guardian registration uses a verified learner link before learner data is
  visible;
- public content becomes progressively database-driven, not a full page builder
  before Phase 1;
- local uploads are the default, with curated external video embeds allowed only
  through an admin-managed allowlist and URL validation;
- Phase 1 registration uses the current serializer fields plus the minimum
  role-specific additions documented in `USER_ROLES_JOURNEYS.md`;
- Phase 1 implementation was approved on 24 November 2026.

The school-admin palette access chosen earlier is retained as `ADMIN` access in
the current model; a custom role needs `appearance.manage`.

## Implementation checks — not blockers

- Administrator and custom-role permissions follow the matrix in
  `USER_ROLES_JOURNEYS.md` and are rechecked before each new admin screen is
  added.
- Production media hosting remains a deployment decision; local storage and
  validated external embeds are the application-level scope for now.

## Do-not-rebuild list

Do not replace or duplicate these while closing gaps:

- the React/Vite + Django/DRF + PostgreSQL architecture;
- the three-experience route split and role redirects;
- custom `User`, role constants, invitations and backend RBAC/scoping;
- institution, learner, teacher, guardian, class, subject and curriculum models;
- course, assessment, attendance, report and communication models;
- existing managed-resource list/form patterns and shared UI components;
- *(removed, do not rebuild)* PWA service worker, mutation queue and manual
  conflict UI;
- runtime theming, palette catalogue, CSS variables and derived chart colours;
  the accessible canvas hero must keep its real `<h1>`;
- backup scripts, seeders, docs structure and bounded external-system rules.

## Phase readiness

| New phase | Baseline | First work once approved |
|---|---|---|
| 0 — Direction/audit | Complete | Await approval to move on |
| 1 — Identity/registration/onboarding | Partial: auth/RBAC strong, onboarding/linking weak | Role-specific forms, verification flows, onboarding records, dedicated approval view |
| 2 — Resource library | Partial: models strong, discovery/upload weak | Taxonomy, upload UX, filters, public/portal catalogue, document library |
| 3 — Academic structure/membership | Mostly present | Consistent CRUD/scoping, enrolment and assignment views |
| 4 — Role dashboards | Baseline analytics only | Four role-specific dashboards |
| 5 — Public content/navigation | Config + theme/logo only | Progressive page/section, navigation, media and announcement models |
| 6 — Assessment/progress/comms | Models strong | Coherent workflows and guardian visibility |
| 7 — Offline hardening | **Superseded/removed** | Do not rebuild; server-side reliability, throttles and honest write failures instead |
| 8 — Branding/settings | Theme manager done | Logo/settings extension only if approved |
| 9 — Verification/handover | Partial | Full regression, deployment/runtime checks and honest limitations |
