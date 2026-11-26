# Admin access guide

This guide explains how to get into the system safely, what each role can do,
and what to do when access goes wrong. It does **not** contain any passwords.
Passwords are set locally, at the keyboard, and never written into a document,
a script or a chat message.

**Current direction:** normal web app only. There is no offline queue, service
worker, PWA or native app; failed saves show an error and remain unsaved.
Sign-in uses an HttpOnly Django session cookie with a readable CSRF cookie
echoed as `X-CSRFToken`. Identity and roles are re-read from
`/api/auth/me/`; no `klb_token` or `klb_user` lives in `localStorage`.
Password changes/resets invalidate active sessions, and reset links expire
after one hour. A normal sign-in lasts one hour of inactivity; activity moves
the expiry forward, and closing the browser does not end it early. Set
`SESSION_COOKIE_AGE=1800` for a 30-minute session. The frontend calls `/api`
through the Vite proxy; the backend allows credentialed CORS from its configured
origins. See `SECURITY_AUDIT.md`.

## 1. Sign in and you land on the right side

There are two UI sides now:

| Side | Address | Who uses it | Layout file |
|---|---|---|---|
| Staff / admin | `/admin/...` | `SUPER_ADMIN`, `ADMIN`, custom roles with `admin.access`, teachers | `frontend/src/layouts/DashboardLayout.jsx` |
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
| `demo_admin` | `ADMIN` (institution administrator) |
| `demo_teacher` | `TEACHER` |
| `demo_learner` | `LEARNER` |
| `demo_guardian` | `GUARDIAN` |
| `platform_admin` | `SUPER_ADMIN` (demo username retained; `SUPER_ADMIN` is unchanged) |

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
.\.venv\Scripts\python.exe manage.py shell -c "from apps.accounts.models import User; u=User.objects.get(username='your_new_admin'); u.role='ADMIN'; u.save(update_fields=['role'])"
```

Replace `your_new_admin` with the username you chose. No password goes into
this command. Set `u.institution` as well for an institution account. For a
custom-role account, assign the role through the user API with
`{ "role": "CUSTOM", "custom_role": <id> }`; user responses include
`custom_role`, `custom_role_name` and `capabilities`.

If password reset email is configured, users can also use
`POST /api/auth/password/reset/`. In local development the reset link is
printed to the console. See `docs/COMMANDS.md` for the full command list.

An administrator can reset another user's account from **Users** with
`POST /api/auth/users/{id}/reset_password/`. The server generates a temporary
password, requires a change at the next sign-in, invalidates the user's old
sessions and writes an audit entry. The temporary password is returned once in
the response: hand it to the account owner securely and never keep it in a
document or chat. The login page has a **Forgot your password?** link, and the
frontend serves `/reset-password` for the email link flow.

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
channels. An `ADMIN` cannot invite into another institution or grant
`SUPER_ADMIN`; only `SUPER_ADMIN` can grant any role.

Teacher self-registration creates an inactive account that an institution
`ADMIN` must approve before sign-in. A signed-in user cannot create another
account: `/register` shows an **Already signed in** state with **Sign out** and
**Go to workspace** options instead of the form.

## 4. Roles and what each one can do

| Role | Scope | What it can do |
|---|---|---|
| `SUPER_ADMIN` | Global | Unrestricted access, including institution management and granting any role. Unchanged by the simplification |
| `ADMIN` | Own institution | Unrestricted CRUD within the institution: people, classes, subjects, reports and the school profile. Can create and assign custom roles; cannot grant `SUPER_ADMIN` or create global institutions |
| `CUSTOM` | Own institution, picked capabilities | Named reusable role identified by `custom_role`; enters `/admin` only with `admin.access`, and every other capability is enforced by the backend |
| `TEACHER` | Own institution | Classes, courses, modules, lessons, questions, assignments, quizzes, exams, attendance and messages; can view learners, but cannot create users or edit the school profile |
| `LEARNER` | Own records | Portal only: courses, textbooks, resources, assignments, quizzes, progress report and profile; may read school identity, may not edit it |
| `GUARDIAN` | Linked learners only | Portal only: reports and messages for learners explicitly linked to the account |

`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER` are
retired names and are no longer assignable. Existing accounts with those values
are migrated to `ADMIN`; the migration never changes, generates or prints a
password. `SUPER_ADMIN` accounts are unchanged. Check the institution on
migrated accounts: with no institution, institution data is hidden by design.

Roles are a string on `accounts.User.role`; custom-role accounts also carry a
`custom_role` id. Permissions come from the role/capability set, not from
`is_superuser` alone.

### Custom-role capabilities

`admin.access`, `users.manage`, `roles.manage`, `academics.manage`,
`learners.manage`, `teachers.manage`, `guardians.manage`, `courses.manage`,
`assessments.manage`, `content.manage`, `attendance.manage`, `fees.manage`,
`communications.manage`, `reports.view`, `appearance.manage`,
`institutions.manage`, `tutor.use`.

Only `admin.access` controls admin-portal entry; the backend enforces the other
capabilities. Custom-role CRUD uses `/api/auth/roles/`, and
`/api/auth/users/roles/` returns the built-ins plus custom options. User
payloads use `{ "role": "CUSTOM", "custom_role": <id> }`; responses include
`custom_role`, `custom_role_name` and `capabilities`.

### Visible identifiers and guardian links

The identifiers shown to people are `TR_SCHOOL_YYYY/MM_NNN` (teachers),
`LR_SCHOOL_YYYY/MM_NNN` (learners) and `GD_SCHOOL_YYYY/MM_NNN` (guardians);
institutions use `INST_YYYY_NNN`. These are display references — database
primary keys and foreign keys stay numeric. Usernames are generated from a
sanitized `first_last` and made unique with a suffix when needed. The
identifiers appear in the Users, Learners, Teachers and Guardians tables. See
`REFERENCE_NUMBERING.md`.

Links are managed from both sides: **Link guardian** on Learners and
**Link learner** on Guardians both post to `/api/learners/guardian-links/`, and
search options show the person's name plus their unique identifier. The dialogs
show existing links, require confirmation before adding another person, and
store academic/attendance/fee access on the link. A pending request for the
selected pair can be verified or rejected inline; all requests are also listed
on the **Guardian links** page. Exactly one guardian can be primary per learner.

### Cross-system tools and capabilities

| Sidebar item | Route | Required backend permission |
|---|---|---|
| Notifications | `/admin/notifications`, `/portal/notifications` | Authenticated; inbox is filtered to the recipient |
| Early warning | `/admin/early-warning` | `reports.view` (built-in staff) or custom role with that capability |
| Fee ledger & receipts | `/admin/fees/ledger` | `fees.manage`; school office only |
| Data quality | `/admin/data-quality` | Institution admin or platform admin; `admin.access` on the route |
| Audit history | `/admin/audit` | Institution admin or platform admin; `admin.access` on the route |

The notification API is deliberately read-only except for explicit mark-read
actions and the user's own preference record. Early-warning tasks can be
assigned only to a user from the same institution. Fee reconciliation uses no
payment-gateway credentials. Data-quality fixes are allowlisted, previewed and
audited; no endpoint deletes a record. Audit rows cannot be created, changed or
deleted through the API.

## 5. Where permissions are configured

| File | What it holds |
|---|---|
| `backend/apps/core/constants.py` | The `Roles` class: built-in role kinds, labels and role groups, and the `Capabilities` allowlist |
| `backend/apps/core/permissions.py` | `can_assign_role()`, `IsContentCurator`, `IsStaff`, `same_institution` and the DRF permission classes |
| `backend/apps/core/viewsets.py` | `InstitutionScopedQuerysetMixin` plus `AdminWriteMixin`, `StaffWriteMixin`, `PlatformWriteMixin`, `ContentWriteMixin`; shared queryset filter and forced `institution` on writes |
| Each app's `views.py` | Per-endpoint overrides in `get_permissions()` (for example `backend/apps/accounts/views.py` and `backend/apps/institutions/views.py`) |
| `backend/apps/institutions/views.py` | The `GET/PATCH /api/institutions/mine/` school-profile action |
| `frontend/src/App.jsx` | Route lists for `/admin` and `/portal`, plus legacy redirects |
| `frontend/src/components/ProtectedRoute.jsx` | Blocks a page when the signed-in role is not allowed |
| `frontend/src/components/RoleHome.jsx` | Redirects old root URLs to the correct side by role; `/` itself is the public homepage |
| `frontend/src/components/ManagedResourcePage.jsx` | Derives create/edit/delete buttons from the endpoint scope and signed-in role; unknown endpoints fail closed |
| `frontend/src/utilities/roles.js` | Shared role sets, role/capability helpers and `homeFor()` used by routes and layouts |

Add a capability to the allowlist in `constants.py` first, then update the
permission helpers, the frontend role utility (`frontend/src/utilities/roles.js`)
and the route guards. Do not scatter role strings through components.

## 6. Cross-institution isolation

This is the central security rule:

- `SUPER_ADMIN` is the only global role and sees all institutions.
- `ADMIN` and custom-role accounts see only rows where `institution_id` matches
  their account.
- A user with **no institution** gets an empty queryset — the system fails
  closed, not open.
- On create and update, the shared mixin overwrites any client-supplied
  `institution` with the signed-in user's institution. A school cannot smuggle
  another school's ID into a payload.
- A record outside the allowed queryset returns **404**, not 403, so the
  existence of another school's record is not revealed.
- Only `SUPER_ADMIN` may create or delete a global institution; `ADMIN` cannot.
- `GET /api/institutions/mine/` is limited to the signed-in user's own school;
  `PATCH` is further limited to administrators.

Tests cover institution-admin visibility, super-admin visibility, cross-school
institution smuggling and school-profile edit rules. See
`docs/TESTING_CHECKLIST.md`.

## 7. Editing the school profile

1. Sign in as `ADMIN` or `SUPER_ADMIN`. A custom role reaches this page only
   when `admin.access` is selected, and any edit is limited to the capabilities
   that role was granted.
2. Open `/admin/school` — **School profile** in the sidebar.
3. Edit the name, phone, email, website, motto or physical address and press
   **Save school details**.
4. To change the logo, choose a JPG, PNG or WebP file of at most 2 MB. The
   upload needs a live connection. If it fails, an error is shown and the
   previous logo stays in place; retry the upload. There is no local queue.

The API behind the page is:

| Method | Endpoint | Who may use it |
|---|---|---|
| GET | `/api/institutions/mine/` | Any signed-in user with an institution, including learners and guardians |
| PATCH | `/api/institutions/mine/` | `SUPER_ADMIN` and `ADMIN` only; custom roles are limited to their capabilities; learners and guardians get HTTP 403 |

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
3. **Account deactivated:** an `ADMIN` can reactivate a user in its own
   institution with `POST /api/auth/users/{id}/set_active/`. `SUPER_ADMIN` can
   do the same for any school.
4. **Wrong school or wrong role:** check `role` and `institution` on the user
   record. An account with no institution sees no institution data by design.
5. **Login succeeded but the page is wrong:** sign out and sign in again. The
   role is always re-read from `GET /api/auth/me/`; the browser does not trust a
   stored role. Old root URLs redirect by role, so use `/admin` or `/portal`
   directly when testing.
6. **Only an admin can fix it and nobody has access:** use local/server access
   to run `changepassword` for an existing admin. Do **not** delete or recreate
   the `lms` database as a quick fix — take a backup first and investigate.

## 9. Safety rules

- Never put a real password in source code, a document, a screenshot or a chat.
- Do not hand-pick passwords for other users. Admin-created accounts start with
  an unusable password; `reset_password` returns one temporary password that
  must be shared securely and never stored in a document or chat. The
  retired-role migration changes only role values: no password is changed,
  generated, printed or stored in a document or chat.
- Errors are professional, field-prefixed messages such as
  `email: This field may not be blank.`; raw JSON is never shown to a user.
- Keep `.env` local and Git-ignored; `.env.example` is the safe template.
  Local secrets are owner-managed and none is in source control.
- `backups/` is Git-ignored: dumps contain password hashes and PII. Take a
  backup with `scripts/backup_database.ps1` before database changes and store
  dumps securely.
- Do not commit or push working changes without review.
- This system is **not production-ready** and is not a substitute for an
  independent security review or the deployment checks in
  `PRODUCTION_CONFIGURATION.md`.
