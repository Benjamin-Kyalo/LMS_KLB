# Functional requirements — Learners Management System

Status: **Target specification**. This describes what the product should do.
`docs/CURRENT_STATE_AUDIT.md` records what already exists and what is missing.

Priority key: **P0** core to the learner-management objective; **P1** important
for a complete product; **P2** enhancement or later phase.

Registration uses the current serializer fields plus the minimum role-specific
additions in `USER_ROLES_JOURNEYS.md` (confirmed 24 November 2026). External
video embeds are permitted only through a curated, admin-managed allowlist with
URL validation.

**Current direction — normal web app only.** Any earlier PWA/offline/native
requirement is superseded: no IndexedDB queue, service worker, PWA manifest,
sync/conflict pages or banners, Capacitor config or native projects. Failed
mutations surface an error and remain unsaved; uploads require a live
connection. Authentication is Django session-cookie based with a readable CSRF
cookie echoed as `X-CSRFToken` and identity/roles always re-read from
`/api/auth/me/`. Security hardening and the remaining deployment checks are in
`SECURITY_AUDIT.md`. A narrow low-bandwidth reversal was documented later:
public read caching and allowlisted theming writes are off by default and never
use a service worker; see `OFFLINE_MODE_REVERSAL.md`.

## A. Public website

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| PUB-01 | Provide a professional public homepage that explains the platform and offers clear role-based entry points | P0 | Homepage loads without sign-in, has one registration route, one sign-in route and no admin navigation |
| PUB-02 | Publish institutional information: story, vision, mission, mandate, leadership and contact routes | P1 | Each topic has a public page or section and can be edited without source changes |
| PUB-03 | Provide a searchable learning-resource catalogue | P0 | Users can search by keyword and filter by level, subject, class and collection; results are paginated |
| PUB-04 | Provide a documents and forms library | P1 | Documents are grouped by category, show title/description/type/date and open or download safely |
| PUB-05 | Publish announcements and educational news | P1 | Items have date, title, category, audience and body; admins can create/edit/delete them |
| PUB-06 | Support video and image resources from the admin panel | P1 | Admin can add, replace and remove local media without code; curated external video embeds use an admin-managed allowlist and validated URLs; public pages render media responsively |
| PUB-07 | Make registration the starting experience for learners, teachers and guardians | P0 | Public register page requires account category before collecting role-specific fields |
| PUB-08 | Provide accessible navigation and readable layouts on all screen sizes | P0 | Desktop, tablet and 390px mobile layouts have no overflow; keyboard and screen-reader labels are present |
| PUB-09 | Preserve SEO metadata and a valid robots.txt | P1 | Meta description, theme colour and robots.txt remain present after content changes |

## B. Registration, onboarding and authentication

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| REG-01 | Learner registration collects learner and guardian basics | P0 | Required fields, validation and duplicate checks are enforced on backend and frontend |
| REG-02 | Teacher registration collects professional details and remains inactive until approval | P0 | New teacher accounts cannot access staff areas until an administrator approves them |
| REG-03 | Guardian registration collects contact details and links to one or more learners | P0 | Guardian sees only linked learners; linking is verified by admin or code before access |
| REG-04 | Administrator accounts are never created through public registration | P0 | Public role choices exclude all admin roles; admin creation uses expiring single-use invitations or the primary admin |
| REG-05 | Each role lands on its own onboarding step and dashboard | P0 | After sign-in, `homeFor(user)` routes to `/admin` or `/portal` and shows a role-specific first-run checklist |
| REG-06 | Users can complete and maintain their own profiles | P1 | Profile changes are scoped to the user and validated; sensitive fields cannot be self-escalated |
| REG-07 | Local password reset/change flows exist without exposing passwords in docs or logs | P0 | `changepassword` and application reset flows are documented; no password is printed or stored in sample data |

## C. Administrator portal

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| ADM-01 | Global and institution administrator scopes are explicit | P0 | A seeded `SUPER_ADMIN` performs every administrative action including institution management and any role grant; `ADMIN` has unrestricted CRUD in its own institution and can create/assign custom roles but cannot grant `SUPER_ADMIN` or create global institutions; custom roles carry only picked capabilities |
| ADM-02 | Full CRUD with search, filter and pagination across managed modules | P0 | Every list supports search/filter/pagination; create, edit and delete are permission-protected and confirmed |
| ADM-03 | Manage learners, teachers, guardians and accounts | P0 | Admin can create, review, approve, suspend and edit users; role changes cannot self-escalate |
| ADM-04 | Manage academic structure | P0 | Institutions, departments, academic years, terms, classes, subjects and timetables are CRUD-managed |
| ADM-05 | Manage learning resources and educational categories | P0 | Admin can create/edit/delete resources, attach files/links and organise by level/subject/class/collection |
| ADM-06 | Manage website pages, images, videos and documents | P1 | Public content sections, media and documents are admin-editable; no source edit is needed for normal changes |
| ADM-07 | Manage navigation menus and sections | P1 | Admin can show/hide/reorder public and portal navigation items within safe, validated keys |
| ADM-08 | Configure dashboards | P1 | Admin can choose which approved cards/modules appear for each role |
| ADM-09 | Manage announcements and notifications | P1 | Admin can publish, schedule, target and retire announcements; in-app notices reflect them |
| ADM-10 | Control branding, colours and visual settings | P0 | Admin can activate seeded palettes, onboard validated palettes and upload logos without component edits |
| ADM-11 | Configure permissions and system settings | P0 | Role rules and the capability allowlist are centralised; custom-role CRUD is at `/api/auth/roles/`, with `admin.access` gating `/admin` and the backend enforcing every other capability; safe settings are stored in the database or env and reflected in the UI |
| ADM-12 | Monitor activities, reports and system performance | P1 | Admin sees audit logs, basic activity reports and health information; no sync/queue health (queue removed) |
| ADM-13 | All admin actions are validated and audited | P0 | Invalid input returns clear field errors; state-changing actions write audit records with actor and entity |

## D. Teacher portal

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| TCH-01 | Dashboard shows assigned classes, learners, resources and due work | P0 | Teacher only sees records linked to their assignments/institution |
| TCH-02 | Manage relevant learning materials and educational content | P0 | Teacher can add/edit resources within assigned scope and attach documents/links |
| TCH-03 | Upload documents and learning resources | P0 | File type/size validation, safe storage and accessible download links |
| TCH-04 | Manage assignments and assessments | P1 | Teacher can create, publish, update and grade within assigned classes |
| TCH-05 | Record and view learner progress | P1 | Attendance, scores and remediation tasks appear in teacher and linked learner/guardian views |
| TCH-06 | Communicate academic information | P1 | Messages/notices are scoped to assigned learners or classes |
| TCH-07 | Maintain own profile and responsibilities | P1 | Teacher can edit permitted profile fields and see assigned subjects/classes |

## E. Learner portal

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| LRN-01 | Dashboard shows subjects, classes, resources, assignments and progress | P0 | Learner only sees their own records and linked resources |
| LRN-02 | Access learning materials and educational resources | P0 | Resources are organised by subject/class/level and open or download correctly |
| LRN-03 | View assignments, assessments and learning activities | P0 | Due work is listed with status, instructions and submission route where supported |
| LRN-04 | Track personal learning progress | P1 | Learner sees attendance, scores, feedback and remediation tasks in plain language |
| LRN-05 | Manage own profile | P1 | Learner can update permitted fields and see school/class information |

## F. Guardian portal

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| GRD-01 | Dashboard shows linked learners and recent updates | P0 | Guardian with no verified link sees an explanatory empty state, never another learner's data |
| GRD-02 | Monitor academic progress and learning activities | P0 | Progress, attendance and reports are read-only and scoped to linked learners |
| GRD-03 | View important school/educational updates | P1 | Announcements targeted to guardians appear with date and category |
| GRD-04 | Access relevant reports and communication | P1 | Reports open with clear labels; messages remain within the guardian's linked scope |

## G. Cross-cutting platform requirements

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| PLT-01 | Backend is authoritative for permissions and institution scoping | P0 | Frontend hiding is never the only control; API tests prove 401/403 and data isolation |
| PLT-02 | Shared records, not duplicate dashboards | P0 | Admin, portal and public views read the same models through serializers/services |
| PLT-03 | Search, filter and pagination on all managed lists | P0 | Lists use DRF pagination/filtering and frontend `useList`/`listAll` consistently |
| PLT-04 | Meaningful empty, loading, success, error and confirmation states | P1 | Every list/form has a designed state; destructive actions require confirmation |
| PLT-05 | Professional buttons and forms | P1 | Hover, active, disabled and loading states are consistent in `global.css` |
| PLT-06 | Responsive and accessible by default | P0 | No horizontal overflow at 390px; labels, focus rings, contrast and semantic controls pass checks |
| PLT-07 | Web reliability without silent data loss (offline PWA requirement superseded) | P1 | A failed mutation shows an error and stays unsaved; the user retries when the connection returns. No local queue, cache or automatic replay |
| PLT-08 | Audit trail for sensitive changes | P1 | User, role, approval, finance and theme changes create audit entries |
| PLT-09 | Labelled sample data for demonstration | P1 | At least 10 labelled samples per category; `.invalid` emails and `sample_` users are clearly marked |
| PLT-10 | Safe boundaries for external systems | P1 | Fees stay ledger-only, KICD internal only, KEMIS local staging only, tutor local/deterministic by default |

## Non-functional requirements

- **Maintainability:** modular Django apps; one shared API contract; no duplicated
  palette literals or role tables.
- **Security:** Django session-cookie authentication with HttpOnly session
  cookie and readable CSRF cookie echoed as `X-CSRFToken`; identity/roles
  re-read from `/api/auth/me/`; PBKDF2 hashing, DB-backed lockout, scoped DRF
  throttles, trusted-proxy-aware `X-Forwarded-For`, one-hour hashed single-use
  reset records, session invalidation on password change/reset, security
  headers and production CSP, scoped reads, magic-byte upload sniffing and
  generic health errors. Production fails closed without
  `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins. Local
  `.env` secrets are owner-managed and `backups/` is Git-ignored; no secret is in
  source control.
- **Performance:** paginated lists, indexed common fields, cached active theme,
  bounded uploads and chart data.
- **Reliability:** database backups before structural migrations; idempotent seeders;
  migrations reviewed before apply; failed writes remain unsaved and visible
  rather than being queued locally.
- **Accessibility:** WCAG AA contrast for text, keyboard navigation, semantic HTML,
  visible focus and plain-language notices.
- **Content governance:** public copy and media are owned by the admin panel or a
  documented config module, never by scattered component literals.

## Out of scope unless explicitly approved

- Copying reference branding, text, images, videos or code.
- Public/admin account creation through open registration.
- Payments, gateways or card storage; fees remain a ledger.
- Native apps entirely: Capacitor config/dependencies and the
  `frontend/android` / `frontend/ios` directories were removed. SMS/USSD
  gateways remain out of scope.
- Deployment, load testing, third-party security review and official KICD/KEMIS submission.
- Destructive demo-data operations without explicit user approval.
