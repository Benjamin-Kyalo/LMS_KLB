# Production configuration

The default settings module (`config.settings`) is safe for local development.
Before exposing the service, use `config.settings_prod`, which inherits the
shared settings and adds strict host, CORS and browser-security defaults.

## 1. Fill the production template

Every secret stays in `.env`, which is Git-ignored. `.env.example` lists the
required keys. At minimum set:

```dotenv
SECRET_KEY=a-fresh-long-random-key
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
`X-Forwarded-Proto: https`.

## 2. Check before starting

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
$env:DJANGO_SETTINGS_MODULE="config.settings_prod"
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py migrate --plan
```

`check --deploy` identified no issues in the verification run recorded in
`TESTING_CHECKLIST.md`. This does **not** deploy the application; a WSGI/ASGI
server, TLS termination, backups and monitoring are still required.

## 3. Build the frontend

```powershell
cd ..\frontend
npm ci
npm run build
```

Serve `frontend/dist` as static files. It contains the generated service
worker and PWA manifest. Configure the host to fall back to `index.html` for
client-side routes.

## 4. Email

Django 6.1 deprecated the old `EMAIL_*` settings. This project uses the new
`MAILERS` setting instead. Development prints messages to the console;
production uses the SMTP values above. Password-reset links use this mailer.

Do not put SMTP credentials in source code.
