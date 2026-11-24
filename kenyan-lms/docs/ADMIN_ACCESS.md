# Admin access guide

This guide explains how to get into the system safely, what each role can do,
and what to do when access goes wrong. It does **not** contain any passwords.
Passwords are set locally, at the keyboard, and never written into a document,
a script or a chat message.

## 1. Sign in and you land on the right side

There are two UI sides now:

| Side | Address | Who uses it | Layout file |
|---|---|---|---|
| Staff / admin | `/admin/...` | Platform admins, school admins, teachers, content managers | `frontend/src/layouts/DashboardLayout.jsx` |
| Learner / guardian portal | `/portal/...` | Learners and guardians | `frontend/src/layouts/PortalLayout.jsx` |

After sign in, the app sends staff to `/admin` and learners or guardians to
`/portal`. The root `/` is the public homepage and does not advertise the
administration portal. Old bookmarks such as `/learners`, `/courses` and
`/reports` still work: `RoleHome.jsx` redirects them by role instead of showing
the wrong layout.

## 2. Demo accounts (usernames only)

Run `.\.venv\Scripts\python.exe manage.py seed_demo` from `backend/` once if
the demo data is missing.

| Username | Role |
|---|---|
| `demo_admin` | School administrator |
| `demo_teacher` | Teacher |
| `demo_learner` | Learner |
| `demo_guardian` | Guardian |
| `platform_admin` | Platform super administrator |

**No demo password is printed here, and none should be pasted into a ticket or
a document.** Set a password you control with `changepassword` (section 3).

## 3. Set or reset a password safely

All commands below are run from `backend/`:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py changepassword demo_admin
```

Django asks you to type the new password twice; nothing is displayed on screen.
Creating a new administrator:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

`createsuperuser` now defaults to role `SUPER_ADMIN`. Permissions still use the
**role** field, not `is_superuser` alone. If you need a different role or
institution, change it deliberately:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from apps.accounts.models import User; u=User.objects.get(username='your_new_admin'); u.role='SCHOOL_ADMIN'; u.save(update_fields=['role'])"
```

Replace `your_new_admin` with the username you chose. No password goes into
this command. Set `u.institution` as well for a school account.

If password reset email is configured, users can also use
`POST /api/auth/password/reset/`. In local development the reset link is
printed to the console. See `docs/COMMANDS.md` for the full command list.

### Invitation-only administrator signup

Public `/register` offers only `LEARNER`, `GUARDIAN` and `TEACHER`. An
administrator account cannot be created there. An authorised admin issues an
invitation at `/admin/invitations`; it fixes the email, role and institution,
expires after seven days, works once and can be revoked. The invitee redeems it
at `/admin/signup` and chooses their own password.

- `POST /api/auth/admin-invitations/` — issue an invitation (admin only).
- `POST /api/auth/admin-invitations/accept/` — redeem a token publicly.
- `DELETE /api/auth/admin-invitations/{id}/` — revoke an unused invitation.

The token is a high-entropy server-side value stored in the database so an
authorised admin can copy it from the invitation list. It is **not** HMAC-signed
or hashed. Treat the token like a credential and do not send it over unsecured
channels. A school admin cannot invite into another institution or grant a
platform role above their own.

Teacher self-registration creates an inactive account that a school
administrator must approve before sign-in.

## 4. Roles and what each one can do

| Role | Scope | What it can do |
|---|---|---|
| `SUPER_ADMIN` | All institutions | Platform-wide access: create institutions, manage all records, manage users |
| `PLATFORM_ADMIN` | All institutions | Same platform-wide access as `SUPER_ADMIN` |
| `INSTITUTION_ADMIN` | Own institution | Manage people, classes, subjects, reports and the school profile; cannot create or delete institutions |
| `SCHOOL_ADMIN` | Own institution | Same as `INSTITUTION_ADMIN`; this is the normal school account |
| `TEACHER` | Own institution | Classes, courses, modules, lessons, questions, assignments, quizzes, exams, attendance and messages; can view learners, but cannot create users or edit the school profile |
| `LEARNER` | Own records | Portal only: courses, textbooks, resources, assignments, quizzes, progress report and profile; may read school identity, may not edit it |
| `GUARDIAN` | Linked learners only | Portal only: reports and messages for learners explicitly linked to the account |
| `CONTENT_MANAGER` | Catalogue | Staff side: textbooks, chapters and resources; publishing through the content endpoints |

Roles are a string on `accounts.User.role`. Platform-level permissions are
decided by that role, not by `is_superuser` alone.

## 5. Where permissions are configured

| File | What it holds |
|---|---|
| `backend/apps/core/constants.py` | The `Roles` class: role codes, labels and role groups |
| `backend/apps/core/permissions.py` | `can_assign_role()`, `IsContentCurator`, `IsStaff`, `same_institution` and the DRF permission classes |
| `backend/apps/core/viewsets.py` | `InstitutionScopedQuerysetMixin` plus `AdminWriteMixin`, `StaffWriteMixin`, `PlatformWriteMixin`, `ContentWriteMixin`; shared queryset filter and forced `institution` on writes |
| Each app's `views.py` | Per-endpoint overrides in `get_permissions()` (for example `backend/apps/accounts/views.py` and `backend/apps/institutions/views.py`) |
| `backend/apps/institutions/views.py` | The `GET/PATCH /api/institutions/mine/` school-profile action |
| `frontend/src/App.jsx` | Route lists for `/admin` and `/portal`, plus legacy redirects |
| `frontend/src/components/ProtectedRoute.jsx` | Blocks a page when the signed-in role is not allowed |
| `frontend/src/components/RoleHome.jsx` | Redirects old root URLs to the correct side by role; `/` itself is the public homepage |
| `frontend/src/components/ManagedResourcePage.jsx` | Derives create/edit/delete buttons from the endpoint scope and signed-in role; unknown endpoints fail closed |
| `frontend/src/utilities/roles.js` | Shared role sets, hierarchy helpers and `homeFor()` used by routes and layouts |

Add a new role in `constants.py` first, then update the permission helpers,
the frontend role utility (`frontend/src/utilities/roles.js`) and the route
guards. Do not scatter role strings through components.

## 6. Cross-institution isolation

This is the central security rule:

- Platform admins (`SUPER_ADMIN`, `PLATFORM_ADMIN`) see all institutions.
- Everyone else sees only rows where `institution_id` matches their account.
- A user with **no institution** gets an empty queryset — the system fails
  closed, not open.
- On create and update, the shared mixin overwrites any client-supplied
  `institution` with the signed-in user's institution. A school cannot smuggle
  another school's ID into a payload.
- A record outside the allowed queryset returns **404**, not 403, so the
  existence of another school's record is not revealed.
- Only platform admins may create or delete an institution.
- `GET /api/institutions/mine/` is limited to the signed-in user's own school;
  `PATCH` is further limited to administrators.

Tests cover school admin visibility, platform admin visibility, cross-school
institution smuggling and school-profile edit rules. See
`docs/TESTING_CHECKLIST.md`.

## 7. Editing the school profile

1. Sign in as `SCHOOL_ADMIN` (or `INSTITUTION_ADMIN` / a platform admin).
2. Open `/admin/school` — **School profile** in the sidebar.
3. Edit the name, phone, email, website, motto or physical address and press
   **Save school details**.
4. To change the logo, choose a JPG, PNG or WebP file of at most 2 MB. The
   upload needs an internet connection; it is not queued offline because file
   uploads cannot be replayed from saved JSON.

The API behind the page is:

| Method | Endpoint | Who may use it |
|---|---|---|
| GET | `/api/institutions/mine/` | Any signed-in user with an institution, including learners and guardians |
| PATCH | `/api/institutions/mine/` | Platform admins and institution/school admins only; others get HTTP 403 |

Logos are saved under `institutions/logos/` and returned as a URL. The user
profile endpoint `GET /api/auth/me/` also returns `institution_logo` (an
absolute URL) and `institution_name`. Both `DashboardLayout` and
`PortalLayout` show that logo, falling back to `/mark.svg` when there is none.

The fields came from migration
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`.
A backup was taken first at `backups/lms_20261123_134452.sql`. Never edit a
migration by hand after it has been applied.

## 8. If you are locked out

Try these in order:

1. **Forgot the password:** from `backend/`, run
   `.\.venv\Scripts\python.exe manage.py changepassword <username>` and type a
   new password twice. Tell the user the account is ready; do not send the
   password in a message.
2. **No account exists:** run
   `.\.venv\Scripts\python.exe manage.py createsuperuser`, then set the role
   with the `shell -c` command in section 3.
3. **Account deactivated:** an institution admin can reactivate a user with
   `POST /api/auth/users/{id}/set_active/`. A platform admin can do the same
   for any school.
4. **Wrong school or wrong role:** check `role` and `institution` on the user
   record. An account with no institution sees no institution data by design.
5. **Login succeeded but the page is wrong:** sign out and sign in again. The
   role is read from `GET /api/auth/me/`; stale browser state can keep the old
   layout visible. Old root URLs redirect by role, so use `/admin` or `/portal`
   directly when testing.
6. **Only an admin can fix it and nobody has access:** use local/server access
   to run `changepassword` for an existing admin. Do **not** delete or recreate
   the `lms` database as a quick fix — take a backup first and investigate.

## 9. Safety rules

- Never put a real password in source code, a document, a screenshot or a chat.
- Do not generate or display passwords for other users; admin-created accounts
  use unusable passwords and the reset flow.
- Keep `.env` local and Git-ignored; `.env.example` is the safe template.
- Take a backup with `scripts/backup_database.ps1` before database changes.
- Do not commit or push working changes without review.
- This system is not a substitute for an independent security review.
