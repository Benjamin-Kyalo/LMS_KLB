# Administrator guide

Staff work in the admin panel at `/admin/...`. Learners and guardians use the
portal at `/portal/...`. See `docs/ADMIN_ACCESS.md` for safe sign-in, password
reset commands and what to do if you are locked out. No passwords are recorded
in these documents.

## Roles and what they can do

| Role | Scope | Key permissions |
|---|---|---|
| `SUPER_ADMIN` | All institutions | Create institutions, all data |
| `PLATFORM_ADMIN` | All institutions | Create institutions, all data |
| `INSTITUTION_ADMIN` | Own institution | Manage people, structure, reports |
| `SCHOOL_ADMIN` | Own institution | Same as above |
| `TEACHER` | Own institution | Classes, courses, assessment, attendance |
| `LEARNER` | Own records | Courses, textbooks, own progress |
| `GUARDIAN` | Linked learners only | Reports and messages |
| `CONTENT_MANAGER` | Catalogue | Publish textbooks (platform-level) |

Learners and guardians only see the portal side; `LEARNER` records are their
own, and `GUARDIAN` records are limited to linked learners. They may read the
school identity but may not edit the school profile.

## Where permissions are configured

- Role codes: `backend/apps/core/constants.py`
- Permission helpers: `backend/apps/core/permissions.py`
- Automatic queryset scoping: `backend/apps/core/viewsets.py`
- Per-view overrides: each app's `views.py` (`get_permissions`)
- School-profile action: `backend/apps/institutions/views.py` (`mine`)
- UI routes and guards: `frontend/src/App.jsx`, `ProtectedRoute.jsx` and
  `RoleHome.jsx` (which redirects old root URLs by role; `/` is the public homepage)

## The isolation rule

A non-platform user is restricted to `user.institution_id` on every
institution-scoped list. Detail access returns 404 rather than 403 where the
object is filtered out of the queryset — this avoids revealing that another
school's record exists. A user with no institution gets an empty queryset.

## Creating a school

1. Sign in as `platform_admin`.
2. Go to `/admin/institutions` (**Institutions → New**).
3. Fill name, code, type ID, county. Create the institution type first via
   `POST /api/institutions/types/` if needed.
4. Create a school administrator account for that institution.
5. The school administrator can then complete contact details and the logo at
   `/admin/school` (**School profile**).

## Editing your own school profile

School and institution admins open `/admin/school`. The page reads and writes
`GET/PATCH /api/institutions/mine/`, so it can only ever affect the caller's
own institution. Editable details include name, phone, email, website, motto
and physical address. The logo must be JPG, PNG or WebP and at most 2 MB.
Upload it while online — it is not added to the offline queue. Learners and
guardians may read the school details but get HTTP 403 if they try to PATCH.

The profile API returns the logo URL as `logo`. The user profile API
`GET /api/auth/me/` returns `institution_logo` (an absolute URL), which both
`DashboardLayout` and `PortalLayout` display with `/mark.svg` as fallback.
The migration that added these fields is
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`;
it was applied after the backup at `backups/lms_20261123_134452.sql`.

## Creating staff and learners

Use **Teachers**, **Guardians** and **Learners** pages. Each create form also
creates the login account, but no password is generated or displayed. The
account is created with an unusable password; use the password-reset flow so
the account owner chooses their own credentials. A local administrator can
also set a password at the keyboard with
`.\.venv\Scripts\python.exe manage.py changepassword <username>` (run from `backend/`).

Admission numbers are generated automatically when the field is left blank.
Official numbers may be supplied manually; duplicates within an institution
return a clear validation message.

## Bulk learner import

`POST /api/learners/bulk-import/` with `{"csv_text": "..."}`.
Required columns: `username, first_name, last_name, admission_number`.
The import runs in one transaction: if any row fails, none are created.

## Academic structure

Academic years, terms, classes and subjects are all configurable. Terms are
not hardcoded to three — private and TVET institutions can use a different
structure. Set `is_current` on the active year and term.

## Content licensing

`content_contentaccess` grants an institution access to a title. Only titles
with status `PUBLISHED` and an active grant appear in
`GET /api/content/available/`. Content managers publish via
`POST /api/content/textbooks/{id}/publish/`.

## Audit trail

Important actions are recorded in `core_auditlog` (user, action, entity,
IP, timestamp). Never delete audit rows.
