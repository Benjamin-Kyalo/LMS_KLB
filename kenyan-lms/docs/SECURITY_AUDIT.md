# Security Audit and Hardening Record

Date: 2026-11-24

## Scope and status

This record covers the existing React/Vite frontend, Django REST Framework backend, PostgreSQL data store, local upload path, and deployment-facing configuration for the Kenyan Learners Management System.

The audit found and remediated multiple high-severity issues. **This document is not a production sign-off.** Deployment/runtime verification is still required, including reverse-proxy header behaviour, TLS, media permissions, least-privilege database access, a shared cache for throttles, SMTP delivery, and `manage.py check --deploy` with production values. The reduced-motion path now has both unit coverage and explicit browser checks under a forced reduced-motion media query; assistive-technology review remains outstanding. Final automated results are recorded in the closeout table.

**Current-state note (post-audit role-model simplification):** the dated audit
records below are retained as history. The current built-in roles are
`SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER` and `GUARDIAN`.
`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER` are
retired and migrated to `ADMIN`; `SUPER_ADMIN` is unchanged. Where older entries
say “platform”, “school” or “institution admin”, read that as `SUPER_ADMIN` or
`ADMIN` under the new model. Passwords are never changed, generated or printed
by the migration. The capability rules are recorded in the next section.

## Verification already performed

- Backend baseline before hardening: `134 passed`.
- Frontend baseline before hardening: `93 passed across 32 files`; production build succeeded with PWA precache entries.
- Frontend after hardening, offline removal and admin photo upload: `101 tests passed across 32 files`; `npm run build` succeeded with no PWA, service-worker, workbox, or manifest artifacts.
- Saved site-content overrides are sanitised on read and write to strip retired offline wording and the `sync` portal nav item; focused theming tests and a browser/API check found no offline terms.
- Frontend dependency audit: `npm audit --audit-level=moderate` reported `0 vulnerabilities`.
- Backend dependency audit: `pip-audit -r requirements.txt` reported no known vulnerabilities after `Pillow` was updated to `13.0.0`.
- Focused backend auth/account/core/tutor/KEMIS/security suite: passing after fixes to throttle override handling, user-list scoping, and tutor provider tests.
- Focused learner/fee/attendance/analytics/institution read-scoping suite: `56 passed` after adding family-scoped reads, profile allowlists, CSV caps, and generic learner-link errors.
- Final full backend suite: `221 passed`; no failures or errors; Django system check identified no issues.
- Production settings check with placeholder production values: `manage.py check --deploy` reported no issues.
- Git-history scan: no actual credentials were found committed; only placeholder names in `.env.example` and documentation.
- Clean production build contains only `index.html`, hashed CSS/JS assets, `robots.txt`, SVG marks, and local images.
- Static browser checks at desktop width and in a 390 px iframe found the accessible `<h1>` visible, one `aria-hidden` canvas, no horizontal overflow, and no manifest link. The only console errors were the expected unauthenticated `/api/auth/me/` and missing local `/api/auth/csrf/` calls because the production build was served without its Django backend.
- Browser checks on `/login` and `/register` confirmed the auth-card entrance animation finishes at the normal transform, button text remains visible during the press animation, and `animationend` removes the pressed class so the standard button state returns. A live session login succeeded, `/portal` loaded under the session cookie, and `localStorage` held no `klb_token` or `klb_user` value.
- Final desktop and 390 px homepage checks against the rebuilt preview plus Django confirmed no offline terms in the rendered page or `/api/theming/site-content/`, one `aria-hidden` canvas, a visible `<h1>`, no manifest link, and no horizontal overflow; the only console error was the expected unauthenticated `/api/auth/me/` 401.
- The reduced-motion fallback is covered by the focused `ParticleHeadline` unit test and by browser checks with `matchMedia` and reduced-motion CSS forced on: at desktop and 390 px the `<h1>` stayed visible with opacity `1`, the canvas stayed `display: none`, `requestAnimationFrame` was never called, and the accessibility tree still exposed the real heading. Assistive-technology review remains outstanding.

## High-severity findings and remediation

| Finding | Risk | Remediation | Verification state |
| --- | --- | --- | --- |
| Public content endpoints exposed unpublished/inappropriate resource fields to ordinary users | Published/unpublished state and sensitive metadata could be enumerated by role | List/retrieve serializers now distinguish manager views from ordinary user views; querysets are scoped; institution and role checks are enforced server-side | Implemented and focused content tests passed |
| Assessment answer keys and cross-school quiz links were exposed | Learners could obtain answers or questions from another institution | Question serialization, quiz visibility, institution scoping, and submission/question relationships were hardened | Final full suite passed `221 tests` |
| Submission, attempt, and lesson-progress fields could be influenced by the client | Grades, completion, and attempt ownership could be falsified | Ownership and institution are derived server-side; writable fields are reduced; progress/results use server-derived values | Final full suite passed `221 tests` |
| Sensitive learner, fee, attendance, and analytics reads were insufficiently scoped | Cross-institution PII and financial/attendance data could be exposed | Read querysets and institution `mine` allowlists were tightened; bulk CSV paths were bounded; learner link errors were generalised | Focused suite passed `56 tests`; final full suite passed `221 tests` |
| `X-Forwarded-For` could bypass login lockout | An attacker could rotate a header to avoid IP-based throttling | `client_ip()` trusts the header only when `REMOTE_ADDR` is in `TRUSTED_PROXY_IPS`; both IP/username and username-only lockout scopes are enforced | Implemented and covered by security tests |
| Production settings were opt-in | Running with local settings in production could leave debug, weak hosts, or console mail enabled | Plain `manage.py` commands now default to local `config.settings`; `wsgi.py` and `asgi.py` still default to `config.settings_prod`; production fails closed without `PRODUCTION_SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `SMTP_HOST` | Implemented; `manage.py check` passes locally and `check --deploy` passed with placeholder values |

## Control-by-control review

### Role model and capability enforcement

- `SUPER_ADMIN` is the only global role: unrestricted access, institution
  management and the ability to grant any role.
- `ADMIN` is unrestricted within its own institution. It may create and assign
  custom roles but cannot grant `SUPER_ADMIN` or create global institutions.
- A `CUSTOM` account names a reusable role through `custom_role` and carries a
  picked capability set. `admin.access` is the only capability that controls
  admin-portal entry; the backend enforces all other capabilities, so hiding a
  UI control never substitutes for a server check.
- Capability allowlist: `admin.access`, `users.manage`, `roles.manage`,
  `academics.manage`, `learners.manage`, `teachers.manage`, `guardians.manage`,
  `courses.manage`, `assessments.manage`, `content.manage`,
  `attendance.manage`, `fees.manage`, `communications.manage`, `reports.view`,
  `appearance.manage`, `institutions.manage`, `tutor.use`.
- Custom-role CRUD is served by `/api/auth/roles/`; `/api/auth/users/roles/`
  returns built-ins plus custom options. User payloads use
  `{ "role": "CUSTOM", "custom_role": <id> }` and responses include
  `custom_role`, `custom_role_name` and `capabilities`, so authorisation is
  always derived from the server-side identity read at `/api/auth/me/`.
- The retired built-in names are removed. Existing accounts are migrated to
  `ADMIN` with their password hash untouched: no password is changed, generated,
  printed or written into documentation.

### Authentication and sessions

- Django's salted, adaptive PBKDF2 password hashing is retained with standard password validators.
- Login now uses the Django session cookie. The session cookie is `HttpOnly`; the CSRF cookie is readable and echoed by the frontend as `X-CSRFToken`.
- Login no longer returns a long-lived bearer token. Existing token authentication remains only for compatibility and tokens are revoked on logout, password change, and reset.
- Identity and roles are always re-read from `/auth/me/`; the frontend no longer trusts cached `klb_token` or `klb_user` values.
- Login failures are counted in the database for both IP/username and username-only scopes with expiry and recovery after the lockout window.
- Password reset links expire after one hour and use hashed, single-use `PasswordResetUse` records. All active sessions and legacy API tokens are invalidated after a successful reset or password change.
- Guardian identifier responses use a generic error to avoid account enumeration.

### Rate limiting and abuse controls

- Scoped DRF throttles cover login, registration, password reset, tutor questions, KEMIS export generation, OneRoster reads (per client id) and unsupported-protocol probes.
- Rates are configured through `DEFAULT_THROTTLE_RATES` and can be tuned through environment variables.
- A shared Django cache is required in multi-worker deployments; the local default is per-process only.
- Health-check database errors return a generic `Database unavailable` response while details go to logs.

### Secrets, configuration, and debug mode

- No secret values are present in source code. Git history contains only placeholder names.
- `.env` is ignored. The Django secret remains locally generated, and the PostgreSQL role password is now owner-designated. `.env` and the PostgreSQL role are aligned to the owner's chosen value and were verified with a live login; no secret is printed in source, docs, logs or chat. The PostgreSQL password must not be rotated again without explicit owner approval.
- The local `.env` must not be copied to a server. Production uses its own `PRODUCTION_SECRET_KEY` and SMTP configuration.
- Backups under `backups/` contain password hashes and personal data; the directory is now ignored. Existing files must be encrypted and stored off-host.
- Production forces `DEBUG = False`, HTTPS redirects/HSTS where configured, secure cookies, and strict host/CORS/CSRF lists.

### Database access control and business logic

- Institution scoping is enforced in querysets and serializers rather than by the client.
- Ordinary users receive reduced field sets; managers retain the full administrative view.
- Submission, quiz-attempt, exercise-attempt, progress, and export paths derive ownership and institution from the authenticated request where applicable. Score, grade, completion, and status fields are server-controlled; grading actions are staff-only.
- Learner-facing question reads omit `correct_answer` and teacher explanations; quiz-question links and quiz attempts are scoped by quiz institution and attempt owner.
- Public library content remains explicitly published-only.
- KEMIS export is local/staging-only by product direction and is now throttled.
- Tutor HTTP calls require HTTPS, an explicit host allowlist, and reject redirects; the local grounded provider remains the default.

### Input validation, XSS, CSRF, and headers

- Profile PATCH uses `UserProfileUpdateSerializer`; email format and field lengths are validated.
- React escaping is retained and canvas text uses a real accessible `<h1>` with a decorative `aria-hidden` canvas.
- CSRF protection is enforced by Django for session-authenticated state-changing requests; the frontend sends `X-CSRFToken`.
- Security headers middleware applies configured headers and `Cache-Control: no-store` to authenticated `/api/` responses.
- Production sets CSP, Permissions-Policy, COOP, CORP, `X-Frame-Options: DENY`, nosniff, and referrer policy. Curated video embeds are explicitly allowlisted in the default CSP.
- Request bodies and uploads are bounded; production defaults cap normal request memory and upload size at 5 MiB.
- Managed photo endpoints and the site-content PATCH require `SUPER_ADMIN` or `ADMIN`, or a custom role whose picked capabilities include `admin.access` and `appearance.manage` (backend-enforced). Uploads accept only JPG/PNG/WebP within 5 MB and ≥640×360 px, check the extension, file bytes and decoded image, write generated filenames under `media/site-content/<slot>/`, and audit every publish, remove and reset. Section styles accept only six-digit hex colours and fixed corner/spacing choices; raw CSS is rejected, saved values are scoped to one section, and a background/text pair must reach 4.5:1 contrast. Semantic status colours stay fixed.
- Built-in palettes are seed data, not executable code. The eight built-in palettes include six supplied-image ramps; Plum Harvest (`plum-harvest`, from `color 7.png`) keeps the exact swatches `#291720`, `#820263`, `#D90368`, `#04A777` and `#FB8B24`, is the current active/fresh-install default after `theming.0004_seed_and_activate_plum_harvest`, and derives AA-safe text shades. Admin edits still pass the same hex-format and 4.5:1 text-contrast validation.

### Dependencies and offline/native removal

- Python and Node dependency audits are clean at the versions recorded above.
- Offline queue code is removed: IndexedDB queue, sync pages/banners, service worker, PWA manifest, workbox precache, React PWA plugin, Capacitor packages/scripts, and `frontend/android` / `frontend/ios`.
- Retired offline wording in saved site-content overrides is replaced on read and write, the old `sync` navigation item is dropped, and admin/resource labels now say “Downloadable” rather than “Offline”.
- By default failed mutations now surface an error and remain unsaved. Uploads require a live network connection. This was a deliberate product change from earlier offline-support documentation.
- A later, separately documented low-bandwidth mode is off by default. When enabled, it caches only public allowlisted reads and queues only allowlisted theming `PATCH`/`DELETE` writes in namespaced `localStorage`. It refuses credential/person-like keys and token-like values, sends `If-Match` with 409 conflicts, and adds no service worker or PWA shell. See `OFFLINE_MODE_REVERSAL.md`.
- Read-only OneRoster clients use env-only secrets, institution pinning, per-client scopes, HS256 assertions and throttling; the tutor adds safe policy metadata and redacted `tutor.*` audit rows. Unsupported LTI/OIDC/JWKS/OAuth routes return a generic 403. No CSP relaxation was made. See `INTEROPERABILITY_AI.md`.
- Existing installs may still have an old service worker. Deployment must include a one-release kill-switch: serve `/sw.js` with no-cache and an unregister/self-delete response, or require users to clear site data.

## Residual deployment tasks

1. Configure a TLS-terminating reverse proxy that sets `X-Forwarded-Proto: https` and is listed in `TRUSTED_PROXY_IPS` when it forwards client IPs.
2. Use a shared Django cache for throttles when running more than one worker.
3. Run PostgreSQL with a least-privilege application role; rotate credentials again if the local role password was ever reused outside this machine.
4. Verify media files are served with correct content types and cannot bypass application/ institution scoping.
5. Configure SMTP and test real password-reset delivery.
6. Run `manage.py check --deploy` with final production values, not placeholders.
7. Complete assistive-technology review; explicit reduced-motion browser checks, static desktop/390 px homepage checks, live login, auth animations, and authenticated `/portal` navigation have passed.
8. Apply the old service-worker kill-switch described above for previously installed clients.

## Deployment verification status

| Item | Verified in code/local checks | Still required at deployment |
| --- | --- | --- |
| TLS and proxy headers | `SECURE_PROXY_SSL_HEADER`, HTTPS redirect/HSTS, trusted-proxy-only `X-Forwarded-For`, and `TrustedProxyHeaderMiddleware` (which strips forwarded HTTPS headers from untrusted peers) are implemented and tested; production refuses an empty `TRUSTED_PROXY_IPS` | Configure a TLS-terminating proxy that sets `X-Forwarded-Proto: https`, list its direct peer in `TRUSTED_PROXY_IPS`, and prevent direct access with a forged header |
| Throttle cache | Scoped DRF throttles and `CACHE_URL` (shared Redis) are implemented; login lockout counters are database-backed and shared; without `CACHE_URL` Django uses a per-process cache | Set `CACHE_URL` to one shared backend, install the Redis client, and confirm both DRF throttles and lockout across workers |
| Database role | `scripts/create_app_db_role.sql` defines `lms_app` with DML/sequence grants; migrations apply cleanly and application queries are scoped in code. The app still uses owner-managed `DB_USER`/`DB_PASSWORD` | Switch the deployed app to the approved least-privilege role, keep migrations under owner credentials, review/revoke excess grants, and rotate only with owner approval |
| SMTP | Production `MAILERS` fails closed without `SMTP_HOST`; placeholder `check --deploy` passed | Configure real server-side SMTP values and send an admin password-reset email end to end, verifying the deployed link target |
| Media | Upload magic-byte sniffing, size bounds, and application scoping are covered by tests; Django serves `/media/` only in `DEBUG` | Configure web-server/proxy media content types and confirm private media cannot bypass application/institution checks |
| CSP host/source list | Production default policy plus `CONTENT_SECURITY_POLICY` override exist; `.env.example` carries a shorter policy without the default embed allowlist | Set the policy for the deployed domain, including `connect-src` for any split API origin, `img-src` for any media CDN, and `frame-src` if embeds are used |
| Secrets handling | `django-environ` reads `.env`; `.gitignore` excludes `.env`/`.env.*` except `.env.example`; Vite exposes only `VITE_*`, used for `VITE_API_BASE_URL` | Inject all secrets server-side only; never print, paste or commit `.env` values, and never prefix a secret with `VITE_` |
| CORS credentials / `/api` proxy | `CORS_ALLOW_CREDENTIALS=True`; production requires explicit `CORS_ALLOWED_ORIGINS`; Vite dev proxy maps `/api` and `/media`; frontend sends `credentials: "include"` | Provide production `/api` and `/media` routes, use exact HTTPS origins (no wildcard with credentials), keep `SameSite` compatibility, and rebuild when `VITE_API_BASE_URL` changes |
| Static files and production build | `STATIC_ROOT` and `npm run build` exist; current `dist` has no PWA artifacts; collectstatic was absent from the deployment flow | Run `collectstatic` with production settings, serve `/static/` from the web server, serve `frontend/dist` with SPA fallback, and verify no stale `/sw.js` is served without the kill-switch |
| Production deploy check | Placeholder `check --deploy` passed with no issues | Repeat with final hosts, origins and secret values |
| Old service worker | `frontend/public/sw.js` ships a one-release self-unregistering kill-switch; current `dist` has no manifest, workbox or precache files | Serve `/sw.js` with `Cache-Control: no-cache` for one release, confirm old workers unregister, then remove the file |
| Accessibility | Lighthouse accessibility `1.00`, accessibility-tree snapshots, visible `<h1>`, and forced reduced-motion browser checks passed | Complete an assistive-technology review with real screen reader/keyboard users |

### Deployment gate re-check (2026-11-26, read-only)

A source/configuration-only re-check confirmed the following. **All ten
deployment concerns are PENDING**; none has been verified against a live
deployment, and no code was changed by this re-check. `.env` was inspected by
key name only — no values were read, printed or copied. The actionable checklist
is in `PRODUCTION_CONFIGURATION.md`, section 5.

| Concern | Repository state | Deployment status |
| --- | --- | --- |
| TLS termination + proxy headers | `TRUSTED_PROXY_IPS` gates `X-Forwarded-For` and forwarded HTTPS headers; production fails closed without it | PENDING |
| Shared throttle cache | Scoped DRF throttles and `CACHE_URL` Redis configuration present; login lockout is DB-backed | PENDING |
| Least-privilege DB role | `lms_app` SQL script exists; app still uses owner-managed `DB_USER`/`DB_PASSWORD` | PENDING |
| SMTP + admin reset email | SMTP env keys and forced production mailer exist; local environment has no `SMTP_*` keys; no end-to-end delivery evidence | PENDING |
| `/media/` serving | `MEDIA_URL`/`MEDIA_ROOT` set; Django route only under `DEBUG` | PENDING |
| CSP host/source list | Override and default policy exist; not tailored to a deployed domain | PENDING |
| Old `/sw.js` | `frontend/public/sw.js` kill-switch exists; still needs deployment and removal after one release | PENDING |
| Secrets server-side | `.env` ignored, env-based settings, browser sees only `VITE_*` values | PENDING for production injection; standing rule not to print/commit values |
| CORS credentials + `/api` proxy | Credentials enabled, explicit production origins required, dev proxy only | PENDING |
| `collectstatic` + production build | `STATIC_ROOT` and build script exist; collectstatic was absent from the deployment flow | PENDING |

## Closeout verification table

| Check | Result |
| --- | --- |
| Full backend suite | `221 passed`; no failures or errors; system check clean |
| Frontend suite | `98 passed across 32 files` |
| Frontend production build | Passed; no PWA/service-worker/manifest artifacts |
| Frontend dependency audit | `0 vulnerabilities` |
| Backend dependency audit | No known vulnerabilities |
| Django system check | Passed |
| Migration drift check | `makemigrations --check --dry-run`: `No changes detected` |
| Production deploy check | Passed with placeholder production values; final values pending |
| Desktop/mobile browser checks | Homepage and 390 px checks passed with no offline terms in page or API response; live session login, auth animations and authenticated `/portal` passed; no `klb_token`/`klb_user` in `localStorage`; forced reduced-motion browser checks passed at desktop and 390 px. Assistive-technology review pending |

**Conclusion:** high-severity issues have concrete remediations in the codebase and the full automated suites pass. Production readiness cannot be asserted until deployment/TLS/proxy/DB/cache/SMTP/media checks, the old service-worker kill-switch, and assistive-technology review are complete.
