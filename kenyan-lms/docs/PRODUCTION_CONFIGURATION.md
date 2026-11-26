# Production configuration

**Current direction:** this is a **normal web app only**. There is no service
worker, PWA manifest, workbox precache, offline queue, Capacitor wrapper or
native build to deploy. The product is **not production-ready**: the checks
below prepare a deployment but do not replace runtime verification.

The default settings module (`config.settings`) is safe for local development.
`config.settings_prod` inherits shared settings and adds strict host, CORS,
session/CSRF, security-header and browser-security defaults. Production
settings now **fail closed**: they require a separate `PRODUCTION_SECRET_KEY`,
an SMTP host, explicit allowed hosts and explicit CORS origins. Do not reuse a
local `.env` on a server.

## 1. Fill the production template

Every secret stays in `.env`, which is Git-ignored. `.env.example` lists the
required keys. Local `.env` remains Git-ignored and owner-managed; no secret is in source
control. At minimum set:

```dotenv
PRODUCTION_SECRET_KEY=a-fresh-long-random-key
DEBUG=False
ALLOWED_HOSTS=lms.your-domain.co.ke
CORS_ALLOWED_ORIGINS=https://lms.your-domain.co.ke
CSRF_TRUSTED_ORIGINS=https://lms.your-domain.co.ke
DB_NAME=lms
# Target role for the pending least-privilege switchover (see section 5.3).
# This is not the currently verified local credential: keep that owner-managed
# value out of docs, scripts and chat.
DB_USER=lms_app
DB_PASSWORD=your-database-password
DB_HOST=127.0.0.1
DB_PORT=5432
TRUSTED_PROXY_IPS=127.0.0.1
FRONTEND_BASE_URL=https://lms.your-domain.co.ke
CACHE_URL=redis://127.0.0.1:6379/1
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=KLB LMS <no-reply@your-domain.co.ke>
```

`SECURE_SSL_REDIRECT` defaults to `True`, HSTS to one year, and secure cookies
to on. If TLS terminates at a reverse proxy, that proxy must send
`X-Forwarded-Proto: https` and must be listed in `TRUSTED_PROXY_IPS`. Production
refuses to start without that list, and `TrustedProxyHeaderMiddleware` strips
forwarded HTTPS headers from any other peer. `FRONTEND_BASE_URL` must be the
public frontend origin so password-reset emails link back to the SPA, and
`CACHE_URL` should point to a shared Redis instance when more than one worker
is running. Set `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and the CSP values
for the real origin. Authentication is Django session-cookie based: the session
cookie is HttpOnly, the CSRF cookie is readable and echoed by the frontend as
`X-CSRFToken`, and identity/roles are re-read from `/api/auth/me/`. No
`klb_token` or `klb_user` is stored in `localStorage`.

## 2. Check before starting

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
$env:DJANGO_SETTINGS_MODULE="config.settings_prod"
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py migrate --plan
```

`check --deploy` has passed with placeholder production values. It does **not**
deploy the application. Re-run it with the final production values. A
WSGI/ASGI server, TLS termination, backups, monitoring and the runtime checks
listed in section 6 are still required.

## 3. Build the frontend

```powershell
cd ..\frontend
npm ci
npm run build
```

Serve `frontend/dist` as static files. The clean web-only build contains only
`index.html`, hashed CSS/JS assets, `robots.txt`, SVG marks and local images.
Configure the host to fall back to `index.html` for client-side routes.

### Manual deployment step: old service-worker kill-switch

Users who installed the service worker before its removal will keep a cached
copy. This is **not app code**. For one release, serve `/sw.js` with
`Cache-Control: no-cache` and a response that unregisters the worker and
self-deletes it (or require those users to clear site data). Without this step
they can still see stale wording or an admin link that the current build does
not render.

## 4. Email

Django 6.1 deprecated the old `EMAIL_*` settings. This project uses the new
`MAILERS` setting instead. Development prints messages to the console;
production uses the SMTP values above. Password-reset links use this mailer,
expire after one hour and are backed by hashed, single-use reset records.
Never put SMTP credentials in source code, and test real delivery before
launch.

## 5. Deployment gate checklist (read-only audit, 2026-11-26)

**Every deployment row below is PENDING.** "Configured in code" means the
mechanism exists in this repository; it is not proof that a live deployment has
it. No `.env` values were read or printed during the audit — only key names were
inspected. Placeholder `check --deploy` results are not deployment sign-off.

| # | Concern | Configured in code (verified) | Status | Acceptance check / action |
| --- | --- | --- | --- | --- |
| 1 | TLS termination and proxy headers | `TRUSTED_PROXY_IPS` gates both `X-Forwarded-For` and forwarded HTTPS headers via `TrustedProxyHeaderMiddleware`; production refuses an empty list | **PENDING** | Proxy terminates TLS, sends `X-Forwarded-Proto: https`, and lists the direct peer in `TRUSTED_PROXY_IPS`. Confirm the app cannot be reached directly with a forged header. |
| 2 | Shared cache for throttles | `CACHE_URL` configures a shared Redis cache; login lockout counters are database-backed | **PENDING** | Set `CACHE_URL` to one shared backend for all workers, install the Redis client, and verify throttle limits across workers. |
| 3 | Least-privilege DB role | `scripts/create_app_db_role.sql` defines `lms_app` with DML/sequence grants; app still reads `DB_USER`/`DB_PASSWORD` from `.env` | **PENDING** | Switch the deployed app to the approved role; keep running migrations as the owner (the script grants no DDL); review/revoke excess table grants. Do not rotate the owner-managed local password without approval. |
| 4 | SMTP and admin password-reset email | `SMTP_*` env keys, production `MAILERS`, fail-closed `SMTP_HOST` check; reset links use `FRONTEND_BASE_URL` | **PENDING** | Set real server-side SMTP values and `FRONTEND_BASE_URL`, then send a real admin reset message end to end and verify delivery and the deployed link target. |
| 5 | `/media/` serving | `MEDIA_URL=/media/`, `MEDIA_ROOT=backend/media`; `static()` is added only when `DEBUG` | **PENDING** | Serve `/media/` through the production proxy or a configured CDN with correct content types; keep private uploads behind application scoping. |
| 6 | CSP host/source list | `CONTENT_SECURITY_POLICY` override and a default policy in `config/settings_prod.py` | **PENDING** | Set the policy for the deployed origin: `connect-src` for any split API origin, `img-src` for any media CDN, and `frame-src` if embeds remain. The shorter policy in `.env.example` omits the default embed allowlist. |
| 7 | Old `/sw.js` after PWA removal | `frontend/public/sw.js` ships a self-unregistering kill-switch; `index.html` registers nothing | **PENDING** | Serve `/sw.js` with `Cache-Control: no-cache` for one release, confirm old workers unregister, then remove the file. |
| 8 | Secrets server-side only | `django-environ` reads `.env`; `.gitignore` excludes `.env`/`.env.*` except `.env.example`; Vite exposes only `VITE_*` | **PENDING** | Inject secrets as server-side environment variables; never print, paste or commit `.env` values, and never give a secret a `VITE_` prefix. |
| 9 | CORS credentials and `/api` proxy | `CORS_ALLOW_CREDENTIALS=True`; production requires explicit origins; Vite dev proxy maps `/api` and `/media`; frontend sends `credentials: "include"` | **PENDING** | Production proxy must forward `/api` and `/media`; list exact HTTPS origins (no wildcard with credentials) and keep cookie `SameSite` compatibility. Rebuild when `VITE_API_BASE_URL` changes. |
| 10 | Static files and production build | `STATIC_ROOT=backend/staticfiles`; `npm run build` script and current `frontend/dist` exist | **PENDING** | Run `collectstatic` with production settings, serve `/static/` from the web server, and serve `frontend/dist` with an SPA fallback to `index.html`. |

### 5.1 TLS and proxy header handling

`TRUSTED_PROXY_IPS` is consulted by `apps.accounts.security.client_ip()` for
`X-Forwarded-For` and by `apps.core.middleware.TrustedProxyHeaderMiddleware`,
which removes forwarded HTTPS headers from untrusted peers before Django's
security middleware runs. `SECURE_PROXY_SSL_HEADER` in
`config/settings_prod.py` trusts `X-Forwarded-Proto: https` only after that
filter, and production refuses an empty trusted-proxy list. The template value
`TRUSTED_PROXY_IPS=127.0.0.1` is for a local loopback proxy, not a deployed
address. Verify the HTTPS redirect and that a spoofed header from an untrusted
address neither enables HTTPS detection nor alters the login lockout key.

### 5.2 Shared cache for rate limiting

`apps/core/throttling.py` uses DRF `SimpleRateThrottle`, which stores counters
in Django's cache. `CACHE_URL` now selects a shared Redis cache for all workers;
without it Django falls back to the per-process local-memory cache. The login
lockout in `apps/accounts/security.py` is stored in PostgreSQL and is already
shared. Point `CACHE_URL` at one shared backend, install the Redis client in the
production image, and verify the `*_THROTTLE_RATE` limits across workers.

### 5.3 Least-privilege database switchover

`scripts/create_app_db_role.sql` creates `lms_app`, grants connect/schema use,
CRUD on existing `public` tables and sequence use, and explicitly says to review
and revoke unnecessary permissions. It does not grant schema/DDL rights, so
`manage.py migrate` must keep using owner credentials until a separate,
approved migration arrangement exists. The running app still takes
`DB_USER`/`DB_PASSWORD` from the environment (the local values are
owner-managed); the script's `APP_PASSWORD` is a placeholder. Switchover means
setting the deployed `DB_USER` to the approved role and supplying its password
from the secret manager, then re-running health and auth checks. Never commit a
filled-in copy of the SQL script and do not rotate the existing local password
without owner approval.

### 5.4 SMTP and password-reset verification

Production forces the SMTP `MAILERS` backend and refuses to start when
`SMTP_HOST` is empty. The local `.env` inspected here has no `SMTP_*` keys; the
template contains placeholders only. Set the real values server-side, re-run
`manage.py check --deploy` with final values, then request a reset for an
administrator test account and confirm the message arrives, opens on the
deployed HTTPS origin, and completes once only. Reset links are built from
`FRONTEND_BASE_URL`; a missing value falls back to the request origin, so set
it explicitly when the API and SPA live on different hosts. Do not paste the
token into logs, chat or documentation.

### 5.5 Media, CSP, old service worker, secrets, CORS and builds

- **Media:** Django only adds `/media/` when `DEBUG=True`. Admin hero photos
  land in `MEDIA_ROOT/site-content/hero/`; a production proxy or CDN must serve
  that path. If a CDN is used, add its host to CSP `img-src`.
- **CSP:** `config/settings_prod.py` uses `CONTENT_SECURITY_POLICY` when set and
  otherwise a default that allows only `'self'` connects, `https:` images and
  the curated video embed hosts in `frame-src`. Copying the shorter `.env.example`
  policy verbatim removes that embed allowlist. Update the policy for the real
  domain rather than weakening `script-src`, `object-src` or `frame-ancestors`.
- **Old service worker:** the rebuilt `dist` has no `sw.js`, manifest or
  workbox files and no registration code. For one release, serve `/sw.js` from
  the edge with `Cache-Control: no-cache` and an unregister/self-delete
  response, or ask affected users to clear site data; then confirm in the
  browser that no worker is registered and remove the route.
- **Secrets:** all Django secrets come from environment/`.env` reads in
  `config/settings.py`. `.env` and `.env.*` are Git-ignored except
  `.env.example`. Vite exposes only `VITE_*` variables to the browser; the
  frontend templates use only `VITE_API_BASE_URL`. Keep every other secret
  server-side and never print or commit `.env` values.
- **CORS / proxy:** `CORS_ALLOW_CREDENTIALS=True` is inherited in production,
  so `CORS_ALLOWED_ORIGINS` must be an explicit list of exact origins, matching
  `CSRF_TRUSTED_ORIGINS`. The Vite `server.proxy` entries for `/api` and
  `/media` are development-only; the production web server must provide those
  routes. Because the session cookie uses `SameSite=Lax`, prefer a same-site
  deployment. `VITE_API_BASE_URL` is read at build time (`/api` in the frontend
  template), so changing it requires a new `npm run build`.
- **Static and build:** the deployment flow had no collectstatic step and no
  static-serving package is pinned in `backend/requirements.txt`. With
  production settings run:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
$env:DJANGO_SETTINGS_MODULE="config.settings_prod"
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py check --deploy

cd ..\frontend
npm ci
npm run build
```

Serve `backend/staticfiles` at `/static/`, serve `frontend/dist` as static
files with an `index.html` fallback for client routes, and never expose
`backend/media` directly if it contains non-public uploads. Repeat the
assistive-technology and deployed-build browser checks when these steps are
complete.

Record each PENDING item as passed with final values before treating the
deployment as production-ready. See `SECURITY_AUDIT.md` for the hardening
record and `TESTING_CHECKLIST.md` for checks already performed.
