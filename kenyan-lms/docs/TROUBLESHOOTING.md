# Troubleshooting

For every issue: identify the exact error, apply the smallest fix, then
confirm with a test or a working request. Never reset the database as a
routine fix.

## PostgreSQL connection fails

**Means:** Django cannot reach the database.

**Likely causes:** wrong `DB_PASSWORD` in `.env`; PostgreSQL service stopped;
BOM at the start of `.env`.

**Identify:**

```powershell
Get-Service -Name '*postgres*'
$env:PGPASSWORD="your-password"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d lms -c "SELECT 1;"
```

**Fix:** start the service, correct `.env`, rewrite `.env` as UTF-8 without BOM.

**Confirm:** `python manage.py check --database default` succeeds and
`GET /api/health/` returns `"database":"connected"`.

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
`VITE_API_BASE_URL=/api`; Vite proxy points at `http://127.0.0.1:8000`.

**Confirm:** `Invoke-RestMethod http://127.0.0.1:8000/api/health/`.

## 401 Unauthorized

**Means:** missing or expired token. Sign out and sign in again. Tokens are
deleted on logout.

## 403 Forbidden

**Means:** your role lacks the permission. Check `ADMIN_GUIDE.md`.

## 404 for a record you know exists

**Means:** institution scoping filtered it out. Confirm the record belongs
to your institution.

## Duplicate admission number returns 400

That is correct behaviour — the API explains which field failed.

## File upload fails

Check `MEDIA_ROOT` exists, the form sends `multipart/form-data`, and the file
is not larger than your web server's limit.

## Tests fail

Read the assertion, identify the failing behaviour, fix the smallest cause,
rerun just that test, then the whole suite. Record the result in
`TESTING_CHECKLIST.md`.
