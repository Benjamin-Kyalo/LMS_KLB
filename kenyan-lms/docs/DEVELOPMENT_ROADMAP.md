# Development roadmap — Learners Management System

Status: **Approved; Phases 1 and 2 implemented**. Phase 0 documentation and all
product decisions were completed on 24 November 2026. Phases 1 and 2 were both
approved and delivered on the same date. Implementation proceeded one module at
a time with tests, preserving working components. Post Phase 2 polish on the
same date added the public book shelf and editable book/resource wording at
`/library`, removed the retired Content managers role preview, and removed the
idle offline status block from the staff and portal shells. **Superseded:**
the PWA write queue and dedicated sync page that remained at that point were
later removed when the product direction changed to a normal web app only.
Phases 3 onward remain future work and are not claimed as complete; current
test totals are in `docs/TESTING_CHECKLIST.md`.

## Rules for every phase

1. Preserve working components; extend or adapt before replacing.
2. One module at a time: design → implement → test → verify → document.
3. Backend permission and validation tests before UI polish.
4. No destructive demo-data change without explicit approval.
5. Back up before structural migrations.
6. Each phase ends with backend tests, frontend tests, build, `manage.py check`
   and a browser check at desktop and 390px mobile.

---

## Phase 0 — Direction, audit and governance

**Status: complete — 24 November 2026.**

**Purpose:** stop feature drift and create shared source-of-truth documents.

**Deliverables**

- Product direction, functional requirements, role/journey, architecture,
  reference review and current-state audit documents.
- Explicit decisions on primary admin scope, registration approval, guardian
  linking, media storage and CMS depth.
- A gap list ranked against P0 requirements.

**Exit criteria**

- User approves the direction and prioritisation.
- Existing functionality is recorded honestly; no working feature is scheduled
  for unnecessary rebuild.

---

## Phase 1 — Identity, registration and onboarding

**Status: complete — 24 November 2026.** Role-specific registration,
inactive-until-approved teachers, verified guardian links, onboarding records and
role-aware landing states are implemented and covered by tests. Administrative
accounts remain invitation-only; public registration cannot create one.

**Purpose:** make registration the starting experience and give every role a
correct first landing state.

**Scope**

- Role-specific registration forms and validation.
- Teacher inactive-until-approval flow.
- Guardian → learner linking and verification.
- Admin invitation flow retained and protected from public registration.
- Onboarding checklist record and per-role first dashboard state.
- Profile completion rules.

**Exit criteria**

- Backend tests prove role restrictions, approval rules and linking scope.
- Frontend tests cover all four registration paths and role-based redirects.
- Browser check covers learner, teacher, guardian and admin entry points.

---

## Phase 2 — Learner-centric resource library

**Status: complete — 24 November 2026 with stated caveats.** The public
catalogue is `/library`; `/resources` keeps a role-aware redirect. A single
`ContentResource` record now carries taxonomy, access scope, local uploads and
validated embeds, with `ResourceCollection` and `EmbedProvider` lookups. Scoped
portal catalogues and a permission-checked download action are implemented.
Large local video hosting, production media serving and third-party embeds
beyond the active allowlist remain deliberate deployment/operations decisions.

**Purpose:** make educational resources easy to find, organise and access.

**Scope**

- Resource taxonomy: level, subject, class, collection, type and access scope.
- Admin CRUD for resources and categories with local upload/link support.
- Curated external video embeds through an admin-managed allowlist with URL
  validation; no arbitrary iframe or script injection.
- Public catalogue with search, filters, sort and pagination.
- Portal resource lists scoped to learner class/subject and teacher assignments.
- Document/forms library and preview/download states.

**Exit criteria**

- A resource can be created in admin and discovered by a learner without code
  changes.
- File validation, allowlist enforcement, empty states and permission boundaries
  are tested.

---

## Phase 3 — Academic structure and membership

**Purpose:** establish the records that make learner management real.

**Scope**

- Institution → department → year → term → class → subject relationships.
- Learner enrolment and teacher assignment records.
- Timetable foundation where missing.
- Admin CRUD, search, filter and pagination for all structures.
- Scoping middleware/queryset mixins applied consistently.

**Exit criteria**

- Admin can build a class, assign a teacher and enroll learners.
- Teacher and learner dashboards show only records from those memberships.
- Institution-isolation tests pass.

---

## Phase 4 — Role dashboards and daily workflows

**Purpose:** replace generic lists with role-relevant working views.

**Scope**

- Admin: approvals, content health, users, reports, system health (no sync
  status — the offline queue was removed).
- Teacher: classes, learners, resources, assignments, messages.
- Learner: subjects, resources, work due, progress.
- Guardian: linked learners, progress, announcements, reports.
- Dashboard card configuration where approved.

**Exit criteria**

- Each dashboard answers “what is mine, what is due, what changed?”
- Mobile layout has no overflow and key actions remain reachable.
- No dashboard exposes another role's private records.

---

## Phase 5 — Admin-managed public content and navigation

**Status: first slice complete on 24 November 2026.** Site wording is now a
single managed document. Platform admins can edit the header, footer, homepage,
role cards, library introduction, sign in and registration copy, and the signed
in brand and portal menu labels at `/admin/site-content`. School admins keep
palette management but cannot change global public copy. Full page sections,
navigation records and media management remain future work.

**Current-state note:** the platform/school split named in this dated phase entry
is superseded. Palette and appearance edits now belong to `SUPER_ADMIN` and
`ADMIN`, or to a custom role with `admin.access` and `appearance.manage`
enforced by the backend. See `USER_ROLES_JOURNEYS.md`.

**Purpose:** remove source-code edits from normal content operations.

**Scope**

- SitePage/Section model for public and portal informational content.
- Navigation item model with validated route keys and visibility.
- Media asset management for images, videos and documents.
- Announcements with audience, category, dates and publish control.
- Progressive migration of static public copy into managed records.

**Exit criteria**

- Admin can change a public page section, image, navigation label and
  announcement without touching source.
- Public SEO metadata, robots.txt and accessibility remain intact.

---

## Phase 6 — Assessment, progress, communication and reports

**Purpose:** connect learning activity to learner progress and guardian visibility.

**Scope**

- Assignments, assessments, submissions and results within assigned classes.
- Attendance and local remediation tasks.
- Messages/notices with strict audience scoping.
- Report snapshots and readable learner/guardian reports.
- Audit log and activity reporting.

**Exit criteria**

- Teacher records progress → learner sees feedback → guardian sees linked report.
- Unauthorised access attempts return 403/404 without leaking data.

---

## Phase 7 — Platform reliability (offline hardening: superseded)

**Purpose:** make low-bandwidth use safe and predictable.

**Historical scope (superseded 24 November 2026):** API cache rules for the
catalogue and active theme, an IndexedDB offline mutation queue with
first-pass optimistic rebase, manual retry/rebase/discard, sync status and
conflict explanations, and physical-device replay if a device were available.
**None of this is in the current product.** The queue, service worker, PWA
manifest and sync/conflict UI were removed; failed mutations now surface an
error and remain unsaved, and uploads need a live connection.

**Current scope**

- Server-side reliability, scoped reads, throttles and health reporting.
- Explicit failure messages and no silent data loss: nothing is saved locally
  when a mutation fails.
- Manual deployment cleanup for previously installed service workers (serve a
  kill-switch `/sw.js` for one release, or have users clear site data).

**Exit criteria**

- Failed writes are visibly unsaved and can be retried by the user.
- Limitations remain documented honestly; no offline/PWA behaviour is promised.

---

## Phase 8 — Branding, settings and polish

**Purpose:** complete admin control of appearance and platform configuration.

**Scope**

- Palette manager already built; confirm scope and extend only if needed.
- Logo and visual settings.
- Safe SystemSetting records with validation.
- Button/state consistency, empty states, loading, success and error patterns.
- Final design-system alignment and accessibility pass.

**Exit criteria**

- Branding changes apply across public, portal, admin, charts and web app
  metadata (`index.html`); there is no PWA manifest to update.
- Design system documentation matches code.

---

## Phase 9 — Verification, documentation and handover

**Purpose:** produce a maintainable, honestly reported product.

**Scope**

- Full backend and frontend suites; build; audit; Django checks.
- Desktop, tablet and 390px browser sweep across all roles.
- Lighthouse accessibility/best-practices/SEO on public pages.
- Update handover, testing checklist, milestones and user guides.
- Record remaining limitations and external dependencies.

**Exit criteria**

- All P0 requirements pass or are explicitly deferred with user approval.
- No commit/push without explicit approval.

---

## Current immediate action

Phase 0, Phase 1 and Phase 2 are complete. The next planned module is Phase 3 —
academic structure and membership. A pre-migration backup was taken at
`backups\lms_20261124_105943.sql` before the Phase 2 structural migration. Any
further migration must still have its own backup. Remaining caveats are recorded
in `docs/TESTING_CHECKLIST.md` and `docs/API_DOCUMENTATION.md`; they are not
implicitly complete. Continue extending the existing registration, RBAC and
content code rather than replacing it.

Current cross-cutting work is security hardening of this web-only product:
session-cookie authentication, scoped reads, throttles and lockout, rotated
local secrets, and the removal of all offline/native scaffolding. Deployment
and runtime verification remain outstanding; see `SECURITY_AUDIT.md`.
