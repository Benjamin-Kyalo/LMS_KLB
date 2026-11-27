# Documentation index

This folder is the operating manual for the project. Every guide reflects
the code that actually exists; unimplemented ideas are labelled as such.
The current product name is **KLB Elimu**, a proposed digital learning
initiative subject to organisational approval; older product names appear only
where they describe historical data or retired roles.

## Two sides of the application

- Staff (`SUPER_ADMIN`, `ADMIN`, custom roles with `admin.access`, teachers)
  work in `/admin/...` using `DashboardLayout`.
- Learners and guardians work in `/portal/...` using `PortalLayout`.
- `/` is the public homepage. It introduces the platform and the supported
  user categories; administrator access is intentionally not advertised there.
- `/library` is the public resource catalogue. Legacy `/resources` keeps a
  role-aware redirect; authenticated readers use the scoped `/portal` lists.
  The managed KLB Elimu public pages include `/for-schools`, `/for-teachers`,
  `/for-learners`, `/for-parents`, `/about`, `/help`, `/contact`, `/faq`,
  `/privacy`, `/terms`, `/acceptable-use` and `/accessibility-statement`.
  `/academic-terms` is the legacy school-term editor; `/terms` is the public
  Terms of Use.
- Sign-in and registration route each role to `/admin` or `/portal`. Old root
  URLs such as `/learners`, `/courses` and `/reports` redirect by role.

See `docs/USER_GUIDE.md` for the day-to-day view and `docs/ADMIN_ACCESS.md`
for safe access and permissions.

## Current product direction — normal web app with narrow low-bandwidth mode

The product direction changed on 24 November 2026: this remains a **normal web
app**, with no PWA or native support. On 26 November 2026 a narrow, env-driven
low-bandwidth mode was added as a documented reversal of the removed write
queue. Earlier documents retain historical context, but every broad
offline/PWA/Capacitor claim below is superseded:

- Still removed: service worker, PWA manifest, workbox precache, Capacitor
  configuration and the `frontend/android` / `frontend/ios` directories.
  `npm run build` produces only `index.html`, hashed CSS/JS assets,
  `robots.txt`, SVG marks and local images.
- By default failed mutations show an error and remain unsaved; uploads require
  a live connection. When `OFFLINE_MODE_ENABLED=True`, an already-loaded page
  may cache a small allowlist of public reads and queue only allowlisted
  `PATCH`/`DELETE` theming writes in `localStorage`. Queued writes carry
  `If-Match`; stale writes surface a 409 conflict instead of overwriting. No
  credentials, CSRF tokens, cookies or person-like fields are stored. See
  `OFFLINE_MODE_REVERSAL.md`.
- **Manual deployment step (not app code):** users who installed the old
  service worker must receive a one-release kill-switch — serve `/sw.js` with
  no-cache and an unregister/self-delete response, or clear site data.
- Authentication uses Django session cookies: an HttpOnly session cookie, a
  readable CSRF cookie echoed as `X-CSRFToken`, and identity/roles always
  re-read from `/api/auth/me/` (the `/auth/me/` endpoint). No `klb_token` or
  `klb_user` values are kept in `localStorage`.
- Security hardening includes retained PBKDF2 hashing, DB-backed login lockout
  plus scoped DRF throttles, trusted-proxy-aware `X-Forwarded-For`, one-hour
  single-use hashed reset tokens, session invalidation on password
  change/reset, security headers and a production CSP, scoped
  content/assessment/course/learner/fee/attendance reads, upload magic-byte
  sniffing and generic health errors. Production settings fail closed without
  a separate `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS
  origins. See `SECURITY_AUDIT.md`.
- The homepage, sign-in and registration headings use an accessible canvas
  particle headline (`frontend/src/components/ParticleHeadline.jsx`) with
  palette-aware gradient colour, a soft halo, a left-to-right settle and a
  legible base `<h1>` beneath the particles. Hover repulsion is a gentle
  shimmer and reconstructs quickly, so headings stay clearly visible before
  and after pointer interaction. Reduced-motion support, responsive resize and
  cleanup are preserved.
- Palette status as of 25 November 2026: Plum Harvest (`plum-harvest`, from
  `color 7.png`) is active and the fresh-install default among eight built-ins;
  earlier Ocean Blue active statements are historical.
- Buttons use a small custom CSS/React interaction layer: `RollingLabel` keeps a
  real accessible label with decorative duplicate text, `AnimatedSubmitButton`
  gives auth submits press feedback, and `HoldToConfirmButton` gives destructive
  actions a hold fill with Enter/Space fallback. Busy states show visible
  rotating labels and set `aria-busy`; focus rings, reduced-motion support,
  dialog semantics, accessible names and fixed status colours (red error,
  green success, amber warning, blue info) are preserved. No new dependency was
  added. See `DESIGN_SYSTEM.md`.
- **Current role model:** built-ins are `SUPER_ADMIN` (global unrestricted,
  institution management and any role grant), `ADMIN` (unrestricted within its
  own institution; can create/assign custom roles; cannot grant `SUPER_ADMIN` or
  create global institutions), `CUSTOM`, `TEACHER`, `LEARNER` and `GUARDIAN`.
  `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER`
  are retired and existing accounts migrate to `ADMIN`; `SUPER_ADMIN` is
  unchanged, and no password is changed, generated or printed. Custom roles pick
  from the capability allowlist, enter `/admin` only with `admin.access`, and
  have every other capability enforced by the backend. The API is
  `/api/auth/roles/` (custom-role CRUD) and `/api/auth/users/roles/` (built-ins
  plus custom options); user payloads use `{ "role": "CUSTOM", "custom_role":
  <id> }` and responses include `custom_role`, `custom_role_name` and
  `capabilities`. See `USER_ROLES_JOURNEYS.md`.
- Rubric grading validates criterion scores on the server, keeps per-attempt
  snapshots, maps totals to achievement bands and publishes feedback to learners
  and permitted guardians. Mastery badges are derived read-only from existing
  competency evidence; no award table is created. See `RUBRICS_MASTERY.md`.
- Interoperability groundwork provides env-only, institution-pinned HS256
  clients and read-only OneRoster-shaped GETs. LTI 1.3, OIDC, JWKS, RS256 and
  OAuth token endpoints are explicitly rejected; no CSP relaxation is made.
  The curriculum tutor returns safe governance metadata and writes `tutor.*`
  audit entries without question or answer text. See `INTEROPERABILITY_AI.md`.
- Local `.env` remains Git-ignored and owner-managed. `backups/` is Git-ignored because dumps
  contain password hashes and PII. **No secret is in source control.**

**Not production-ready.** Deployment/runtime verification is still required:
proxy headers, TLS, media-serving permissions, least-privilege DB, a shared
cache for throttles, SMTP, `manage.py check --deploy`, and assistive-technology
review. Reduced-motion browser checks have passed under forced media at desktop
and 390 px. Current verification figures are in `TESTING_CHECKLIST.md`.

## Product foundation — read first

| Document | Purpose | Status |
|---|---|---|
| `PRODUCT_DIRECTION.md` | Vision, mission, objectives, users, decisions and the feature test | Approved foundation |
| `REFERENCE_REVIEW.md` | What was reviewed on the KLB and Zeraki sites and what may be incorporated | Written |
| `FUNCTIONAL_REQUIREMENTS.md` | Target functional and non-functional requirements | Written |
| `USER_ROLES_JOURNEYS.md` | Current role taxonomy, capabilities, migration mapping and registration/daily journeys | Updated for the simplified role model |
| `SYSTEM_ARCHITECTURE.md` | Target architecture, domain model and data flows | Written |
| `DESIGN_SYSTEM.md` | Approved palette, semantic tokens and UI conventions | Written |
| `CURRENT_STATE_AUDIT.md` | What exists now and the gaps against the target | Written |
| `PROGRESS_AUDIT.md` | Done, pending and recommended improvements after the current hardening pass | Written |
| `DEVELOPMENT_ROADMAP.md` | Phased implementation sequence and exit criteria | Approved; Phases 1–2 complete |

## Documents

| Document | Purpose | Status |
|---|---|---|
| `README.md` | This index | Written |
| `SYSTEM_OVERVIEW.md` | Architecture and request flow | Written |
| `DESIGN_SYSTEM.md` | Colour palette, contrast ratios and UI conventions | Written |
| `OCEAN_PALETTE.md` | Approved blue-only palette, exact extracted values and semantic decision | Written |
| `REFERENCE_MODELS.md` | Five reference systems, borrowed ideas, original design, accessibility and low-bandwidth guidance | Written |
| `ASSET_CREDITS.md` | Locally hosted photographs, original SVG and reference-use statement | New |
| `PUBLIC_SITE_CONTENT.md` | Admin-managed KLB Elimu content pack: header, footer, homepage sections, public pages, messages, library, auth, portal wording, migrations and style allowlist | Updated |
| `REFERENCE_NUMBERING.md` | Automatic admission, staff and other business codes | Written |
| `INSTALLATION_GUIDE.md` | Step-by-step setup on Windows | Written |
| `COMMANDS.md` | Complete PowerShell command list with working directories | Written |
| `PRODUCTION_CONFIGURATION.md` | Production settings (fail-closed), TLS, CORS, mail, optional low-bandwidth/interop env keys and old service-worker kill-switch | Updated |
| `DATABASE_GUIDE.md` | Tables, relationships, migrations, backups | Written |
| `FILE_STRUCTURE_GUIDE.md` | Folder structure and important files | Written |
| `USER_GUIDE.md` | How each role uses the system | Updated for `/admin` and `/portal` |
| `ADMIN_GUIDE.md` | Roles, permissions, institutions and school profile | Updated |
| `ADMIN_ACCESS.md` | Safe admin access, roles, invitation-only admin signup, isolation, locked-out help | Updated |
| `SAMPLE_DATA.md` | Labelled sample records, counts, idempotent seeder and caveats | New |
| `TROUBLESHOOTING.md` | Common errors and fixes | Written |
| `BACKUP_AND_RESTORE.md` | Safe backup and recovery | Written |
| `API_DOCUMENTATION.md` | Endpoints, roles/capabilities, custom-role CRUD, onboarding/verification, public enquiries and review queue, resource discovery, school profile and frontend usage | Updated for the simplified role model |
| `RUBRICS_MASTERY.md` | Rubric builder, criterion marking, publication, resubmission and mastery evidence | New |
| `OFFLINE_MODE_REVERSAL.md` | Documented narrow reversal of the 24 Nov removal: public cache, allowlisted writes, conflicts and exclusions | New; off by default |
| `INTEROPERABILITY_AI.md` | Env-only HS256 OneRoster groundwork, rejected protocols and governed tutor policy | New |
| `SECURITY_AUDIT.md` | Hardening record, verification performed and outstanding deployment tasks | Written; not a production sign-off |
| `TESTING_CHECKLIST.md` | Tests actually run and pending tests | Updated |
| `HANDOVER_REPORT.md` | Status, verification and known limitations | Updated |
| `MILESTONES_AJ.md` | A–J historical milestone record; offline/PWA/native items are superseded | Historical — superseded in part |
| `NATIVE_WRAPPER.md` | Short removal notice: the Capacitor wrapper and native projects no longer exist | Superseded |

## How to use these documents

- New to the project? Read the product foundation table above first, then
  `SYSTEM_OVERVIEW.md` and `INSTALLATION_GUIDE.md`.
- Need to run a command? Use `COMMANDS.md`.
- Need admin access or a password reset? Use `ADMIN_ACCESS.md`.
- Something broken? Start with `TROUBLESHOOTING.md`.
- Need to understand a table? Use `DATABASE_GUIDE.md`.
- Need an endpoint? Use `API_DOCUMENTATION.md`.
- Want the honest completion status? Use `PROGRESS_AUDIT.md`,
  `CURRENT_STATE_AUDIT.md`, `HANDOVER_REPORT.md` and `TESTING_CHECKLIST.md`. Older delivery docs use an
  earlier phase numbering where 0–6 are mostly implemented, 7 was a PWA/mobile
  foundation, 8 is partial and 9 is incomplete. **Phase 7 PWA/native work
  was subsequently removed**; do not mix those labels with the new product
  phases in `DEVELOPMENT_ROADMAP.md`.
- Historical docs may name `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`,
  `SCHOOL_ADMIN` or `CONTENT_MANAGER`. Those entries are retained as dated
  history; current state uses `ADMIN` (or `SUPER_ADMIN`) and named custom roles.

No password belongs in any of these files. Use
`python manage.py changepassword <username>` or `createsuperuser` locally.
