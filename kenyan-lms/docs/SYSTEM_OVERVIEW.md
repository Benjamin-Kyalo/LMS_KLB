# System overview

**Current direction — normal web app only.** There is no offline queue,
service worker, PWA manifest, workbox precache, Capacitor configuration or
native wrapper. `npm run build` emits only `index.html`, hashed CSS/JS assets,
`robots.txt`, SVG marks and local images. Failed mutations show an error and
remain unsaved; uploads require a live connection. Earlier descriptions of
queued writes, sync banners and cached pages were accurate historically but are
superseded. See `README.md` and `SECURITY_AUDIT.md`.

## Two UI sides

The React app has two shells over the same API:

| Side | Base URL | Layout | Used by |
|---|---|---|---|
| Staff admin panel | `/admin/...` | `frontend/src/layouts/DashboardLayout.jsx` | `SUPER_ADMIN`, `ADMIN`, custom roles with `admin.access`, teachers |
| Learner / guardian portal | `/portal/...` | `frontend/src/layouts/PortalLayout.jsx` | Learners and guardians |

`/` is the public homepage in `frontend/src/pages/Home.jsx`; its hero uses
`frontend/src/components/ParticleHeadline.jsx`, which draws particles on a
canvas while keeping the real `<h1>` text in the DOM. The canvas is
`aria-hidden`, respects `prefers-reduced-motion`, repels pointer/touch input,
resizes responsively and cleans up on unmount. The homepage does not advertise
the internal administration portal. Sign-in and registration route each role to
the right side, and `RoleHome.jsx` handles old root URLs such as `/learners`,
`/courses` and `/reports`. `frontend/src/App.jsx` defines the routes and guards;
`ProtectedRoute.jsx` blocks a role that does not belong on that side. Both
layouts read the school name and `institution_logo` from `/api/auth/me/` and
show `/mark.svg` if no logo has been uploaded.

## The components

| Component | Django apps | Responsibility |
|---|---|---|
| **SIS** | `accounts`, `institutions`, `learners`, `teachers`, `guardians`, `academics`, `attendance` | People, classes, timetables, attendance |
| **LMS** | `courses`, `assessments`, `curriculum` | Teaching, learning, quizzes, exams, CBE outcomes |
| **Publishing** | `content` | Textbooks, chapters, resources, exercises, licences |
| **Cross-cutting** | `core`, `communications`, `reports`, `theming` | Permissions, audit, messages, dashboards, palettes, site content |

## How a request travels

1. React sends a JSON request, e.g. `GET /api/learners/`, with its session
   cookie. State-changing requests also send `X-CSRFToken` from the readable
   CSRF cookie.
2. Django REST Framework authenticates the session and applies the default
   `IsAuthenticated` permission. Legacy token auth remains only for
   compatibility.
3. The ViewSet's `InstitutionScopedQuerysetMixin` narrows the queryset:
   `SUPER_ADMIN` sees everything; `ADMIN` and custom-role accounts see only
   their institution. A user with no institution sees **nothing** (fail closed).
4. Content, assessment, course, learner, fee and attendance reads apply scoped
   querysets and reduced field sets for ordinary users.
5. The serializer converts model rows to JSON; React renders the result. Vite
   proxies `/api` to Django during development.

```text
React (5173) --session cookie + CSRF--> Django REST (8000) --ORM--> PostgreSQL "lms"
```

Failed writes return an error and are not saved locally. There is no retry
queue, sync banner or conflict page; the user decides whether to try again.

## Institution isolation — the central security rule

`apps/core/viewsets.py` contains one mixin used by almost every ViewSet.
It filters on `institution_id` for everyone except `SUPER_ADMIN`. Object-level
checks and capability enforcement also exist in `apps/core/permissions.py`.
Tests prove that an institution `ADMIN` cannot see another school's learners or
courses, and gets a 404 for another school's course detail page.

The same mixin forces `institution` on create and update, so a client cannot
smuggle another school's ID into a payload. A project-wide smoke test loads
every list endpoint to catch wiring errors before deployment.

The institution ViewSet is a deliberate exception because an `Institution`
does not have an `institution` field of its own. Its `get_queryset()` limits
`SUPER_ADMIN` to all schools and everyone else to their own school. The
`mine` action adds a second check: only `SUPER_ADMIN` and `ADMIN` may PATCH the
profile (custom roles are limited to their capabilities). Learners and guardians
can GET it but receive HTTP 403 on PATCH.

## School profile and logo

`Institution` stores `phone`, `email`, `website`, `motto` and `logo` in
addition to the existing identity and address fields. The migration
`apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`
was applied after a backup (`backups/lms_20261123_134452.sql`). A logo upload is
multipart, JPG/PNG/WebP, at most 2 MB, and server-side magic-byte sniffing
validates the bytes. It needs a live connection because failed uploads are not
saved or replayed. `GET /api/auth/me/` returns `institution_logo` so both
layouts can render the same image.

## Reference numbers

Admission numbers, staff numbers, course/subject codes and other business
identifiers are generated by `apps/core/codes.py`. The generator uses
PostgreSQL advisory locks so concurrent requests cannot issue the same
number. Formats are documented in `REFERENCE_NUMBERING.md`; official codes
supplied by a user are preserved.

## Authentication and security

- Custom user model `accounts.User` (extends Django's `AbstractUser`) adds
  `role`, `institution`, `phone`, `preferred_language` and a legacy
  `must_change_password` flag. Admin-created accounts use an unusable password
  instead of a generated temporary one.
- Login sets an HttpOnly Django session cookie and a readable CSRF cookie; the
  frontend echoes the latter as `X-CSRFToken`. Identity and roles are always
  re-read from `/api/auth/me/` (the `/auth/me/` endpoint). No `klb_token` or
  `klb_user` values are stored in `localStorage`.
- PBKDF2 password hashing and validators are retained. Login failures are
  counted in the database (IP/username and username-only scopes), and scoped
  DRF throttles cover login, registration, reset, tutor and KEMIS paths.
  `X-Forwarded-For` is trusted only from configured proxy IPs.
- Reset links expire after one hour and use hashed, single-use records;
  successful password change/reset invalidates active sessions and legacy
  tokens. In local development reset links are printed to the console.
- Production adds security headers and a CSP, and fails closed without a
  separate `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins.
- Local `.env` remains Git-ignored and owner-managed, `backups/` is Git-ignored because dumps
  contain hashes/PII, and no secret is in source control. See
  `SECURITY_AUDIT.md` for the full hardening record.

## Roles

Built-ins: `SUPER_ADMIN` (global unrestricted, including institution management
and granting any role), `ADMIN` (unrestricted within its own institution; can
create/assign custom roles, cannot grant `SUPER_ADMIN` or create global
institutions), `CUSTOM`, `TEACHER`, `LEARNER`, `GUARDIAN`.

`CUSTOM` is a named reusable role with a `custom_role` id and picked
capabilities from `apps/core/constants.py`. It enters `/admin` only with
`admin.access`; the backend enforces the remaining capabilities. Custom-role
CRUD is at `/api/auth/roles/`, and `GET /api/auth/users/roles/` returns built-ins
plus custom options. User payloads use `{ "role": "CUSTOM", "custom_role":
<id> }`; responses include `custom_role`, `custom_role_name` and `capabilities`.

The retired `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and
`CONTENT_MANAGER` names are removed and those accounts migrate to `ADMIN` with
passwords untouched; `SUPER_ADMIN` is unchanged. See `USER_ROLES_JOURNEYS.md`.

## Completion and verification status

Phase 0–6 are mostly implemented on the original delivery roadmap. The former
Phase 7 (offline/mobile) work was **removed**, not completed. Phase 8 is
partial: bounded local fees, approval, KEMIS, tutor and analytics modules
exist, but no official integration or hosted AI provider is configured.
Phase 9 is not complete.

Frontend verification after hardening: **101 tests across 32 files**, a clean
web-only build and `npm audit --audit-level=moderate` with **0 vulnerabilities**.
The focused backend auth/account/core/tutor/KEMIS/security suite passes
(**71 tests**) and the full backend suite passes (**221 tests**).
**This project is not production-ready**: proxy headers, TLS, media serving
permissions, least-privilege DB, a shared throttle cache, SMTP, final
`manage.py check --deploy` values and assistive-technology checks still need
verification; reduced-motion browser checks have passed under forced media at
desktop and 390 px. See `HANDOVER_REPORT.md` and `TESTING_CHECKLIST.md`.

## Why a modular monolith?

All apps live in one Django project and one PostgreSQL database. This keeps
local development simple, transactions reliable and debugging understandable.
App boundaries are explicit, so a module can later be extracted if needed —
without a rewrite now.
