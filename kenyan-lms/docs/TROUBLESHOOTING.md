# Troubleshooting

For every issue: identify the exact error, apply the smallest fix, then
confirm with a test or a working request. Never reset the database as a
routine fix.

**Current direction:** normal web app only. There is no offline queue, service
worker, PWA install or native app. Failed saves show an error and stay unsaved;
uploads require a live connection. If a user still sees old cached wording or a
stale bundle, the cause is an installed **old** service worker from before the
removal. That is a deployment cleanup, not app code: serve a one-release
kill-switch `/sw.js` with no-cache and an unregister/self-delete response, or
have the user clear site data (see `PRODUCTION_CONFIGURATION.md`). If low-bandwidth
mode is enabled, check its allowlists and conflict screen before blaming the
network; see `OFFLINE_MODE_REVERSAL.md`.

## PostgreSQL connection fails

**Means:** Django cannot reach the database.

**Likely causes:** wrong `DB_PASSWORD` in `.env`; PostgreSQL role password out
of sync with `.env`; PostgreSQL service stopped; BOM at the start of `.env`.
If the role and `.env` drifted apart, run
`powershell -ExecutionPolicy Bypass -File .\scripts\set_postgres_password.ps1`
from an Administrator PowerShell. It reads the password from `.env`, restores
`pg_hba.conf`, and never prints the secret.

**Identify:**

```powershell
Get-Service -Name '*postgres*'
$env:PGPASSWORD="your-password"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d lms -c "SELECT 1;"
```

**Fix:** start the service, correct `.env`, rewrite `.env` as UTF-8 without BOM.

**Confirm:** `python manage.py check --database default` succeeds and
`GET /api/health/` returns `"database":"connected"`.

### pgAdmin still shows `password authentication failed for user "postgres"`

This is a **saved client password** problem, not a table-permission problem. The
server role and `.env` are already aligned and verified with a direct login.
In pgAdmin:

1. Select the server in Object Explorer.
2. Use **Object → Clear Saved Password** (or right-click the server → **Clear Saved Password**).
3. Right-click the server → **Connect…**, type the current password, and tick
   **Save Password** only after the connection succeeds.
4. Expand the **`lms`** database → **Schemas → public → Tables** to see this
   application's tables. Other databases in the tree do not contain them.

## `fe_sendauth: no password supplied`

**Means:** SCRAM authentication needs a password. Supply `PGPASSWORD` or fix
`.env`; do not change `pg_hba.conf` to trust connections.

## Migration errors / missing tables

**Identify:** `python manage.py showmigrations`.

**Fix:** `python manage.py migrate`. If a migration is genuinely broken, take
a backup first and edit the migration deliberately — never drop tables by hand.

**Confirm:** `python manage.py migrate` reports "No migrations to apply".

## `ModuleNotFoundError`

**Means:** a package is missing from the active Python environment.

**Fix:** activate `.venv` and run `python -m pip install -r requirements.txt`.

## npm / Vite errors

**Means:** dependencies missing or Node version too old.

**Fix:** `npm install`, confirm `node --version` is 20+. If `npm run build`
fails after an install, delete `node_modules` and `package-lock.json`, then
`npm install` again (this does not touch project data).

## API communication fails in the browser

**Means:** frontend cannot reach Django.

**Check:** Django running on 8000; `.env` in `frontend/` has
`VITE_API_BASE_URL=/api`; Vite proxy points at `http://127.0.0.1:8000`. The
frontend calls `/api` through that Vite proxy with credentialed CORS; earlier
auth failures were caused by this proxy/CORS path and are fixed by this setup —
keep both in place rather than switching to an absolute API host.

**Confirm:** `Invoke-RestMethod http://127.0.0.1:8000/api/health/`.

## API returns a stale serializer error after a code change

**Means:** the running backend process still has the old serializer loaded.

**Fix:** restart the backend process, then retry the request; serializer and
validation changes are not picked up until Django reloads.

**Confirm:** the response matches the current serializer.

## 401 Unauthorized

**Means:** the Django session is missing or expired, or the CSRF header was not
sent. Sign out and sign in again; the frontend echoes the CSRF cookie as
`X-CSRFToken`. Identity and roles are re-read from `/api/auth/me/`, not from
browser-stored credentials. Repeated failures can trigger the database-backed
lockout; wait for the lockout window or have an administrator reactivate the
account.

## 403 Forbidden

**Means:** your role lacks the permission. Check `ADMIN_GUIDE.md`.

## 404 for a record you know exists

**Means:** institution scoping filtered it out. Confirm the record belongs
to your institution.

## Duplicate admission number returns 400

That is correct behaviour — the API explains which field failed.

## File upload fails

Check the connection is live (failed uploads are not queued or replayed), the
form sends `multipart/form-data`, `MEDIA_ROOT` exists and the file is within the
size limit. The server sniffs magic bytes, so the content must really be JPG,
PNG or WebP for a logo or an allowed type for a resource; renaming a file does
not pass validation. Managed public-site photos must additionally be at least
640×360 pixels and at most 5 MB; per-section styles accept allowlisted values
only and raw CSS is rejected. A failed save rolls back cleanly — no partial
record or file is left behind (see `DATABASE_GUIDE.md`).

## Tests fail

Read the assertion, identify the failing behaviour, fix the smallest cause,
rerun just that test, then the whole suite. Record the result in
`TESTING_CHECKLIST.md`.
