# File structure guide

```text
kenyan-lms/
├── backend/
│   ├── config/          settings.py, urls.py, asgi.py, wsgi.py
│   ├── apps/
│   │   ├── core/        shared permissions, base models, health check, audit
│   │   ├── accounts/    user model, auth endpoints, passwords
│   │   ├── institutions/ schools (incl. profile/logo), years, terms, classes, subjects
│   │   ├── learners/    learner profiles, guardians links, transfers, CSV import
│   │   ├── teachers/    staff profiles, allocations, lesson plans
│   │   ├── guardians/   parent profiles
│   │   ├── academics/   timetable and events
│   │   ├── attendance/  daily records and bulk marking
│   │   ├── curriculum/  version-aware CBE framework
│   │   ├── courses/     courses, modules, lessons, assignments, submissions
│   │   ├── assessments/ questions, quizzes, attempts, exams, results
│   │   ├── content/     textbooks, chapters, resources, exercises, licences
│   │   ├── communications/ announcements, messages, notifications
│   │   └── reports/     dashboards and learner reports
│   ├── manage.py        Django command-line entry point
│   └── requirements.txt pinned Python packages
├── frontend/
│   ├── public/          manifest.webmanifest, mark.svg
│   └── src/
│       ├── components/  reusable UI (ChartCard, DataTable, Modal, PortalList,
│       │                ProtectedRoute, RoleHome, ResourcePage, ...)
│       ├── layouts/     DashboardLayout (staff /admin shell) and
│       │                PortalLayout (learner/guardian /portal shell)
│       ├── pages/       one file per screen; Portal*.jsx are portal pages,
│       │                SchoolProfile.jsx edits the school's own record
│       ├── services/    api.js (JSON + multipart upload), auth.js,
│       │                offlineQueue.js — all HTTP lives here
│       ├── hooks/       useApi, useOnlineStatus, useSyncQueue
│       ├── context/     AuthContext, ToastContext
│       ├── utilities/   roles.js, format.jsx
│       ├── styles/      tokens.css and global.css
│       └── test/        Vitest setup
├── docs/                the guides you are reading (see docs/README.md),
│                        including ADMIN_ACCESS.md, COMMANDS.md,
│                        REFERENCE_MODELS.md and MILESTONES_AJ.md
├── scripts/             PowerShell environment, backup and restore helpers
├── .env.example         safe template (committed)
├── .env                 real values (never committed)
└── .gitignore
```

## School profile data

The `Institution` JSON includes `phone`, `email`, `website`, `motto` and a
`logo` URL. The profile page is `frontend/src/pages/SchoolProfile.jsx`; the
API action is `/api/institutions/mine/`. User JSON from `/api/auth/me/` also
includes `institution_logo`, which both layouts use. The logo field was added
by
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`,
applied after the backup `backups/lms_20261123_134452.sql`.

## What to edit when

| Change | File |
|---|---|
| Add a role | `backend/apps/core/constants.py` + `frontend/src/utilities/roles.js`, then update permission helpers and route guards |
| Change colours / typography | `frontend/src/styles/tokens.css` |
| Add an API endpoint | the app's `views.py` + `urls.py` |
| Change a database field | the app's `models.py`, then `makemigrations` (back up first) |
| Add a staff page | `frontend/src/pages/` + a route under `/admin` in `App.jsx` + nav in `DashboardLayout.jsx` |
| Add a learner/guardian page | `frontend/src/pages/` + a route under `/portal` in `App.jsx` + nav in `PortalLayout.jsx` |
| Change the landing page by role | `frontend/src/components/RoleHome.jsx` |
| Change school profile fields/logo rules | `backend/apps/institutions/models.py`, `serializers.py`, `views.py`, `frontend/src/pages/SchoolProfile.jsx` |
| Change allowed frontend origins | `backend/config/settings.py` (`CORS_ALLOWED_ORIGINS`) |
| Change a dependency | `backend/requirements.txt` or `frontend/package.json` |

## Files you should not edit by hand

- Generated migrations under `apps/*/migrations/`
- `frontend/dist/`, `frontend/node_modules/`
- `backend/.venv/`, `backend/logs/`
- `frontend/public/sw.js` (rebuilt on `npm run build`)
