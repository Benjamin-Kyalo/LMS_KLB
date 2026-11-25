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
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=127.0.0.1
DB_PORT=5432
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=KLB LMS <no-reply@your-domain.co.ke>
```

`SECURE_SSL_REDIRECT` defaults to `True`, HSTS to one year, and secure cookies
to on. If TLS terminates at a reverse proxy, that proxy must send
`X-Forwarded-Proto: https` and must be trusted for `X-Forwarded-For` (see
`TRUSTED_PROXY_IPS`); otherwise client-IP lockout and throttles cannot be
trusted. Set `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and the CSP values
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

## 5. Runtime verification still required

- Reverse proxy sets `X-Forwarded-Proto: https` and a trusted
  `X-Forwarded-For`; TLS is valid end to end.
- Media files are served with correct content types and cannot bypass
  application/institution scoping; `DEBUG` media serving is not a plan. Admin
  hero-photo uploads land under `MEDIA_ROOT/site-content/hero/`, so either serve
  `/media/` through the proxy or point `MEDIA_URL` at a configured CDN and allow
  that host in the CSP `img-src` policy.
- PostgreSQL runs with a least-privilege application role.
- A shared Django cache is configured for DRF throttles when more than one
  worker is running.
- SMTP delivery is confirmed with a real reset message.
- `manage.py check --deploy` passes with final, non-placeholder values.
- Assistive-technology behaviour is reviewed. Desktop and 390 px browser
  checks already passed for console errors, overflow, protected routes and the
  reduced-motion canvas fallback under forced media; repeat them against the
  deployed build.

See `SECURITY_AUDIT.md` for the hardening record and `TESTING_CHECKLIST.md`
for the verification actually performed.
