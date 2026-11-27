# System architecture — Learners Management System

Status: **Target architecture**, preserving the existing modular-monolith
approach. `docs/CURRENT_STATE_AUDIT.md` records the actual baseline and gaps.

**Current direction — normal web app only.** All offline/PWA/native layers have
been removed: no IndexedDB mutation queue, service worker, PWA manifest,
workbox precache, Capacitor wrapper or `frontend/android` / `frontend/ios`.
The architecture below reflects that removal. References to queued writes or
cached/offline paths are historical. Failed mutations surface an error and stay
unsaved; uploads require a live connection. The old service worker is handled
by a manual deployment kill-switch (see `PRODUCTION_CONFIGURATION.md`). A later
narrow, env-driven low-bandwidth module adds public read caching and allowlisted
theming writes without reviving PWA/native layers; see
`OFFLINE_MODE_REVERSAL.md`.

## Architectural principles

1. **One product, one backend, one database.** Public site, authenticated portal
   and administration are route/permission experiences, not separate products.
2. **Learner at the centre.** Academic records, resources, communication and
   reports relate back to a learner, class or subject.
3. **Backend authoritative.** Permissions, validation, institution scoping and
   audit live in Django/DRF; the React UI mirrors them only for usability.
4. **Shared contracts.** One serializer/viewset per resource; every frontend
   surface consumes the same API.
5. **Configurable before code-editable.** Content, media, navigation, branding
   and safe settings belong in admin-editable records or documented config.
6. **Honest failure.** There is no local write queue: a failed mutation shows
   an error and remains unsaved. The server stays authoritative.
7. **Bounded integrations.** Fees, KICD, KEMIS and tutor stay inside their
   approved local/internal limits.

## Logical layers

```
Browser (normal web app)
  Public pages (/)      Portal (/portal/*)      Admin (/admin/*)
          React Router + role guards + layouts + shared components
                         |
       ThemeProvider / AuthContext / ToastContext / ParticleHeadline
                         |
              services/api.js (HTTP + CSRF + multipart)
                         |
                 DRF REST API (/api/...)
                         |
      Auth | Core | Academics | Content | Resources | Assessments |
      Attendance | Reports | Communications | Guardians | Fees |
      Approval | KEMIS | Tutor | Analytics | Theming
                         |
           PostgreSQL `lms`  +  local media storage
```

## Backend domain map

Target domain relationships. Existing apps should be extended rather than
duplicated; new records are added only where a requirement has no owner.

### Identity and access

- **User** — username, role (`SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`,
  `LEARNER`, `GUARDIAN`), optional `custom_role`, institution, profile fields,
  active/approval state. User responses expose `custom_role`,
  `custom_role_name` and the effective `capabilities`.
- **CustomRole** — named reusable role with picked capabilities; CRUD at
  `/api/auth/roles/`, options at `/api/auth/users/roles/`.
- **AdminInvitation** — expiring, single-use, server-side token with fixed role
  and institution.
- **ApprovalRecord** — teacher approval, guardian link verification and related
  state transitions.
- **AuditLog** — actor, action, entity, institution, details, timestamp, IP.

Rules: `SUPER_ADMIN` has unrestricted global control, including institution
management and granting any role; `ADMIN` has unrestricted CRUD within its own
institution and may create/assign custom roles but cannot grant `SUPER_ADMIN` or
create global institutions; a `CUSTOM` account carries only its picked
capabilities and enters `/admin` only with `admin.access`, with the backend
enforcing every other capability. No self-escalation; public registration
excludes admin roles. Retired `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`,
`SCHOOL_ADMIN` and `CONTENT_MANAGER` accounts are migrated to `ADMIN` with
passwords untouched; `SUPER_ADMIN` is unchanged.

### Academic structure

- **Institution** → **Department** → **AcademicYear** → **Term**
- **Class** belongs to institution/year and is linked to subjects and learners.
- **Subject** belongs to institution/department and can be taught by teachers.
- **Course** → **Module** → **Lesson** organises structured learning content.
- **Enrolment** links learner to class/year/term.
- **TeacherAssignment** links teacher to class/subject.
- **TimetableEntry** schedules class/subject/teacher/time.

### Learning resources

- **ResourceCategory / Collection** — CBE, Secondary, Revision, Readers,
  Tertiary or custom categories.
- **Level / Grade** — Grade 1–9, Form 1–4, Tertiary, etc.
- **LearningResource** — title, description, subject, level, class, collection,
  type, file/link/video, status, access rules and tags.
- **MediaAsset** — uploaded image/video/document used by public pages, notices
  and resources; curated external embeds are stored as validated allowlisted
  URLs, never arbitrary iframe or script markup.
- Resource access can be public, institution-scoped, class-scoped or
  learner/group-scoped.

### Learning activity

- **Assignment** and **Assessment** belong to class/subject/teacher.
- **Submission** belongs to learner and assignment.
- **Result / Grade** belongs to learner and assessment.
- **AttendanceRecord** belongs to learner, class and date.
- **RemediationTask** is derived by local rules from snapshots; it is advisory,
  not an AI decision.
- **ReportSnapshot** stores computed report data for fast, bounded display.

### Communication

- **Announcement** — title, body, category, audience, publish dates, media.
- **Message** — sender, recipient/audience, institution scope, read state.
- **Notice** — short system or user-facing notification.

### Public site and configuration

- **SitePage / Section** — admin-managed public or portal content.
- **NavigationItem** — label, route/key, group, visibility, order.
- **Document** — public document/forms library entry with file metadata.
- **ThemePalette** — nine ramp shades, active flag, audit fields.
- **SystemSetting** — safe, validated key/value configuration owned by admin.

### Bounded external domains

- **Fees** — structures, invoices, recorded payments and ledger only.
- **KICD** — internal approval workflow only; no official submission.
- **KEMIS** — local export staging only; no transmission or credentials.
- **Tutor** — deterministic/local by default; optional env-only HTTP provider.

## API contract

- REST over JSON, DRF routers and explicit action routes.
- Django session-cookie authentication: HttpOnly session cookie, readable CSRF
  cookie echoed as `X-CSRFToken`. Identity/roles are re-read from
  `/api/auth/me/`; no `klb_token` or `klb_user` in `localStorage`. Legacy token
  auth remains only for compatibility and is revoked on logout/password change.
- Consistent list contract: pagination, `search`, `filterset_fields`, `ordering`.
- Explicit action endpoints for non-CRUD transitions: approve, link learner,
  activate palette, publish announcement. There is no replay-conflict endpoint.
- State-changing actions create audit records where required.
- Public endpoints are read-only and contain no private records.

Main prefixes: `/api/auth/`, `/api/theming/`, `/api/core/`, `/api/academics/`,
`/api/content/`, `/api/assessments/`, `/api/attendance/`, `/api/reports/`,
`/api/communications/`, `/api/guardians/`, `/api/learners/`, `/api/teachers/`,
`/api/institutions/`, `/api/approval/`, `/api/fees/`, `/api/kemis/`,
`/api/tutor/`, `/api/analytics/`.

## Frontend structure

- `App.jsx` defines three route groups: public `/`, staff `/admin/*`, portal
  `/portal/*`.
- `DashboardLayout` and `PortalLayout` provide distinct navigation and identity.
- `Guard`/`ProtectedRoute` enforce role gates after `/auth/me/` resolves.
- `AuthContext`, `ThemeContext`, `ToastContext` hold cross-cutting state.
- `services/api.js` is the only HTTP client; reads and writes go straight to
  the API. Failed writes surface an error and remain unsaved.
- Authentication helpers use the CSRF cookie and `/api/auth/me/` rather than
  browser-stored credentials.
- `hooks/useApi.js` standardises list/detail loading, errors and reloads.
- `components/` holds shared tables, forms, charts, notices, badges, dialogs and
  empty states; feature pages compose them instead of duplicating markup.
- `styles/tokens.css` defines semantic aliases; `ThemeProvider` supplies runtime
  `--ramp-*` values, so no component hardcodes a palette.
- `components/ParticleHeadline.jsx` renders the accessible canvas hero: the
  real `<h1>` stays in the DOM, canvas is `aria-hidden`, reduced motion is
  respected, pointer/touch repulsion and responsive resize are supported, and
  listeners/frames are cleaned up.
- No PWA layer: the build emits only `index.html`, hashed CSS/JS, `robots.txt`,
  SVG marks and local images.

## Key data flows

### Publish a learning resource

Admin selects resource → uploads file/link/video, sets level/subject/class/
collection and access scope → server validates and stores → public/portal list
queries use the same record → audit entry written.

### Register and onboard a teacher

Public role choice → role-specific form → inactive user created → admin approves
and assigns classes → teacher signs in → onboarding checklist → teacher dashboard.

### Guardian links a learner

Guardian registers → proposes learner identifier/code → admin or verification
rule confirms link → guardian portal queries through linked-learner scope.

### Activate a palette

Admin applies palette → server atomically switches the single active record →
frontend `refreshTheme()` fetches active palette → CSS variables, charts and
meta theme colour update.

### Failed write (offline write flow superseded)

User submits an edit with no connection → the API call fails → the UI shows an
error and the change remains unsaved → the user retries when the connection
returns. There is no queue, `If-Match` replay or conflict screen. The old
offline-write flow was removed with the PWA.

## Configuration ownership

| Kind | Owner | Examples |
|---|---|---|
| Secrets/env | `.env` + `.env.example` | DB credentials, optional tutor endpoint |
| Django settings | code | Installed apps, auth, CORS, media paths |
| Database records | admin panel | Users, resources, pages, notices, palettes, settings |
| Frontend config file | documented module | Public footer preview text until moved into admin content |
| Static assets | repo/public | Logos, approved SVG artwork, robots.txt, local images (no manifest shell) |

## Quality attributes

- **Security:** RBAC + institution scoping on backend, session cookies with
  HttpOnly/CSRF handling, identities re-read from `/api/auth/me/`, PBKDF2,
  DB-backed lockout and scoped throttles, trusted-proxy-aware
  `X-Forwarded-For`, one-hour hashed single-use reset records, session
  invalidation on password change/reset, security headers and production CSP,
  scoped reads, magic-byte upload sniffing, generic health errors, expiring
  invitations, no secrets in source, audit trail. Production fails closed
  without `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins;
  local `.env` remains Git-ignored and owner-managed; `backups/` is Git-ignored.
- **Accessibility:** semantic HTML, labelled controls, visible focus, AA text
  contrast, plain-language errors and notices.
- **Performance:** indexed common filters, pagination, cached active theme,
  bounded uploads and charts.
- **Maintainability:** one owner per fact, modular apps, documented contracts,
  tests per module before moving on.
- **Resilience:** backups before migrations, idempotent seeders, visible
  unsaved-write errors, and deterministic local fallback for external services.
- **Deployment verification (outstanding):** proxy headers, TLS, media
  permissions, least-privilege DB, shared throttle cache, SMTP and
  `manage.py check --deploy`, plus browser/assistive-technology checks.
  Production readiness is not claimed.
