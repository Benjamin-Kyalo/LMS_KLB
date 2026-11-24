# Installation guide (Windows)

The project lives at:

```text
C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms
```

## 1. Confirm prerequisites

```powershell
python --version
node --version
npm --version
git --version
```

Expected: Python 3.13+, Node 20+, npm 10+, Git 2.40+.

PostgreSQL 18 should be running on port 5432:

```powershell
Get-Service -Name '*postgres*' | Select-Object Name, Status
```

## 2. Database and environment

The `lms` database already exists. If you are on a new machine, create it:

```powershell
$env:PGPASSWORD="your-postgres-password"
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -w -h 127.0.0.1 -p 5432 -U postgres lms
```

Copy the template and set your password:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms"
Copy-Item .env.example .env
notepad .env
```

Set `DB_PASSWORD` to your local password. `.env` is Git-ignored — never commit it.

## 3. Backend

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Expected: `System check identified no issues`, migration lines ending `OK`,
and `Starting development server at http://127.0.0.1:8000/`.

## 4. Frontend (second terminal)

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\frontend"
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. If you ran `seed_demo`, the school administrator
username is `demo_admin`. Set or reset its password locally with
`python manage.py changepassword demo_admin` from `backend/`; see
`ADMIN_ACCESS.md`.

## 5. Verify the chain

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health/
```

Expected JSON: `"status":"ok"`, `"database":"connected"`.

## 6. Run tests

```powershell
cd ..\backend
python -m pytest

cd ..\frontend
npm test
npm run build
```

## 7. Production

The steps above are for local development. Before public exposure, follow
`PRODUCTION_CONFIGURATION.md`. It selects `config.settings_prod`, requires
explicit hosts and CORS origins, enables TLS/security headers and configures
the Django 6 `MAILERS` SMTP backend. Run
`python manage.py check --deploy` with that settings module and record the
result before deployment.

## Common setup mistakes

- **BOM in `.env`** — use `notepad` or ensure UTF-8 without BOM. A BOM makes
  the first key unreadable.
- **Wrong working directory** — `manage.py` must be run from `backend/`.
- **Password in source code** — never; it belongs only in `.env`.
