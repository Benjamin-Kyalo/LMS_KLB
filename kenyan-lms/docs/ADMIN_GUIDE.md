# Administrator guide

Staff work in the admin panel at `/admin/...`. Learners and guardians use the
portal at `/portal/...`. See `docs/ADMIN_ACCESS.md` for safe sign-in, password
reset commands and what to do if you are locked out. No passwords are recorded
in these documents.

**Current direction:** normal web app, not a PWA or native app. The broad
offline mutation queue, service worker, PWA manifest and native wrapper were
removed. Failed saves show an error and remain unsaved; uploads require a live
connection. A narrow env-driven mode may be enabled for public read caching and
allowlisted theming writes with visible conflicts; see
`OFFLINE_MODE_REVERSAL.md`. Authentication uses HttpOnly session cookies with
`X-CSRFToken`, and identity/roles are re-read from `/api/auth/me/`. Content,
assessment, course, learner, fee and attendance reads are scoped server-side.
The frontend uses `/api` through the Vite proxy and the backend allows
credentialed CORS from configured origins. See `SECURITY_AUDIT.md`.

Rubric grading, publication and derived mastery badges are documented in
`RUBRICS_MASTERY.md`. OneRoster clients and the governed tutor are read-only
integration surfaces documented in `INTEROPERABILITY_AI.md`; they require
server-side environment configuration and do not change normal staff roles.

## Roles and what they can do

| Role | Scope | Key permissions |
|---|---|---|
| `SUPER_ADMIN` | Global | Unrestricted access, including institution management and granting any role |
| `ADMIN` | Own institution | Unrestricted CRUD, including creating/assigning custom roles; cannot grant `SUPER_ADMIN` or create global institutions |
| `CUSTOM` | Own institution, picked capabilities | Named reusable role with a `custom_role` id; enters `/admin` only with `admin.access`, and the backend enforces the other capabilities |
| `TEACHER` | Own institution | Classes, courses, assessment, attendance |
| `LEARNER` | Own records | Courses, textbooks, own progress |
| `GUARDIAN` | Linked learners only | Reports and messages |

`PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER` are
retired names; existing accounts are migrated to `ADMIN` without changing or
printing passwords. `SUPER_ADMIN` is unchanged. Custom roles pick from
`admin.access`, `users.manage`, `roles.manage`, `academics.manage`,
`learners.manage`, `teachers.manage`, `guardians.manage`, `courses.manage`,
`assessments.manage`, `content.manage`, `attendance.manage`, `fees.manage`,
`communications.manage`, `reports.view`, `appearance.manage`,
`institutions.manage` and `tutor.use`. They are managed at `/api/auth/roles/`;
`/api/auth/users/roles/` lists built-ins plus custom options.

Learners and guardians only see the portal side; `LEARNER` records are their
own, and `GUARDIAN` records are limited to linked learners. They may read the
school identity but may not edit the school profile.

People see `TR_SCHOOL_YYYY/MM_NNN` (teacher), `LR_SCHOOL_YYYY/MM_NNN` (learner)
and `GD_SCHOOL_YYYY/MM_NNN` (guardian) identifiers; institutions use
`INST_YYYY_NNN`. These are display references, while database primary and
foreign keys stay numeric. Usernames are sanitized `first_last` values made
unique with a suffix. The identifiers appear in the Users, Learners, Teachers
and Guardians tables. See `REFERENCE_NUMBERING.md`. A signed-in user cannot
create another account: `/register` offers **Sign out** and **Go to workspace**
instead of a form.

## Where permissions are configured

- Role codes: `backend/apps/core/constants.py`
- Permission helpers: `backend/apps/core/permissions.py`
- Automatic queryset scoping: `backend/apps/core/viewsets.py`
- Per-view overrides: each app's `views.py` (`get_permissions`)
- School-profile action: `backend/apps/institutions/views.py` (`mine`)
- UI routes and guards: `frontend/src/App.jsx`, `ProtectedRoute.jsx` and
  `RoleHome.jsx` (which redirects old root URLs by role; `/` is the public homepage)

## The isolation rule

Every user other than `SUPER_ADMIN` is restricted to `user.institution_id` on
institution-scoped lists. Detail access returns 404 rather than 403 where the
object is filtered out of the queryset — this avoids revealing that another
school's record exists. A user with no institution gets an empty queryset.

## Creating a school

1. Sign in as `SUPER_ADMIN`.
2. Go to `/admin/institutions` (**Institutions → New**).
3. Fill name, code, type ID, county. Create the institution type first via
   `POST /api/institutions/types/` if needed.
4. Create an `ADMIN` account for that institution (`ADMIN` cannot create global
   institutions).
5. That administrator can then complete contact details and the logo at
   `/admin/school` (**School profile**).

## Editing your own school profile

`ADMIN` and `SUPER_ADMIN` open `/admin/school`. The page reads and writes
`GET/PATCH /api/institutions/mine/`, so it can only ever affect the caller's
own institution. Editable details include name, phone, email, website, motto
and physical address. The logo must be JPG, PNG or WebP and at most 2 MB, with
server-side magic-byte validation. Upload it with a live connection: a failed
upload shows an error and is not saved, so retry it. Learners and guardians may
read the school details but get HTTP 403 if they try to PATCH.

The profile API returns the logo URL as `logo`. The user profile API
`GET /api/auth/me/` returns `institution_logo` (an absolute URL), which both
`DashboardLayout` and `PortalLayout` display with `/mark.svg` as fallback.
The migration that added these fields is
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`;
it was applied after the backup at `backups/lms_20261123_134452.sql`.

## Creating staff and learners

Use **Teachers**, **Guardians** and **Learners** pages. Each create form also
creates the login account, but no password is generated or displayed at that
point. The account is created with an unusable password; use the password-reset
flow so the account owner chooses their own credentials. A local administrator can
also set a password at the keyboard with
`.\.venv\Scripts\python.exe manage.py changepassword <username>` (run from `backend/`).

Admission numbers are generated automatically when the field is left blank.
Official numbers may be supplied manually; duplicates within an institution
return a clear validation message. Errors are shown as professional,
field-prefixed messages such as `email: This field may not be blank.`, never raw
JSON.

An administrator can reset a user from **Users** with
`POST /api/auth/users/{id}/reset_password/`. It generates one temporary
password, requires a change at the next sign-in, invalidates the user's old
sessions and writes an audit entry. Share the temporary password securely; do
not store it in a document or chat. Users can recover their own account from
the login page's **Forgot your password?** link and the `/reset-password` route.

## Guardian links

Links can be made from either side. **Link guardian** on Learners and
**Link learner** on Guardians both post to `/api/learners/guardian-links/`;
search options show a name plus the unique identifier. The Learners and
Guardians tables show a `Linked` or `Not linked` badge; where a link already
exists, the action becomes **Add guardian** or **Add learner**.

After a person is selected, the dialog shows their identifying details and any
other learners/guardians already linked on either side. An exact duplicate is
blocked with a clear message. Otherwise, an administrator must tick **I have
reviewed the existing links above and want to continue** before saving. Choose
access to academic records, attendance and fee information; fee access is off by
default. Only one guardian can be primary for a learner — choosing **Yes** for
**Primary link** replaces the earlier primary link.

A pending request for the exact pair can be verified or rejected inline in the
same dialog, or from the **Guardian links** page. Rejection requires a short
reason. Verification creates or confirms the grant, records the decision in the
audit log, and only then does the guardian see the learner in the portal.

## Bulk learner import

`POST /api/learners/bulk-import/` with `{"csv_text": "..."}`.
Required columns: `username, first_name, last_name, admission_number`.
The import runs in one transaction: if any row fails, none are created.

## Academic structure

Academic years, terms, classes and subjects are all configurable. Terms are
not hardcoded to three — private and TVET institutions can use a different
structure. Set `is_current` on the active year and term.

## Rubric marking and feedback release

Staff with `courses.manage`, `assessments.manage` or built-in teacher/admin access use
`/admin/rubrics` to build school templates: name the rubric, add percentage achievement bands, add
scored criteria and save reusable feedback phrases. Global templates are platform-owned and cannot be
changed by a school. `/admin/assignments` optionally links an assignment to a rubric and sets whether
resubmission is allowed and how many attempts a learner gets.

`/admin/submissions` opens a marking grid when the assignment has a rubric. Scores are checked against
each criterion's maximum and the server totals them; it then resolves the achievement band from the
final percentage and snapshots criterion marks per attempt. Later rubric edits do not rewrite past
grades. Saving a grade leaves feedback private; **Publish feedback** releases it and notifies the
learner plus verified guardians with academic access. Private staff notes are never shown outside
staff views. `/portal/submissions` lets learners read published feedback and send another attempt
while attempts remain. Every build, grade, publication and resubmission is audit-logged. See
`RUBRICS_MASTERY.md`.

## Content licensing

`content_contentaccess` grants an institution access to a title. Only titles
with status `PUBLISHED` and an active grant appear in
`GET /api/content/available/`. Staff with `content.manage` (an `ADMIN` or a
custom role with that capability) publish via
`POST /api/content/textbooks/{id}/publish/`.

Public-site wording, photos and theme palettes remain editable from
`/admin/appearance`; the retired public-site `content` / “Content managers”
cards stay retired and cannot be restored from cached overrides.

## Cross-system tools

The **Insights & quality** sidebar group holds five staff tools. Notification
inbox links appear in **Overview** for staff and in the learner/guardian portal
navigation.

### Notification centre

`/admin/notifications` and `/portal/notifications` show only the signed-in
user's alerts. Unread counts, **Mark read** and **Mark all as read** are the only
writes; users cannot invent, edit or delete notifications. The preferences
panel saves `in_app`, `email`, `sms` and an optional list of allowed types. An
empty type list means every event is allowed. Notifications are emitted by
server workflows such as guardian links, fee payments and early-warning
refreshes.

### Early warning

`/admin/early-warning` recalculates transparent, additive rules over existing
records. Attendance over 20% absent in 30 days scores 3, a result below 50%
scores 3, one overdue assignment scores 2, low lesson completion scores 2 and an
invoice more than 7 days overdue scores 1. Scores of 6+, 3–5 and 1–2 are high,
medium and low. Open **Evidence** to see the exact threshold, each signal's
points and the suggested action. **Recalculate warnings** creates one
intervention task per medium/high learner who does not already have an open
task; staff can assign it to themselves, complete it or dismiss it. Dismissing
never deletes the evidence.

### Mastery badges

`/admin/mastery` shows derived badge displays alongside the mastery evidence
already recorded by staff. Scores are averaged per learner and competency using
the shared 0–1 bands; achieving and extending are earned, while beginning and
developing show progress. Staff cannot create, edit or award a badge here: the
screen is read-only and never creates a notification or audit entry. Learners
see their own badges at `/portal/mastery`; guardians do not have a badge view.

### Fee ledger and receipts

The school office uses `/admin/fees/ledger`. It reads the same invoices and
payments as the existing fee pages, shows totals and reconciliation exceptions,
and opens a printable receipt derived from a recorded payment. Receipt numbers
are the payment `reference`; no separate receipt table was added. Mobile-money
payments recorded without a transaction code stay in an exception state until
an office user checks the message and enters the code in **Reconcile**. A code
can only be used once per school. This application never stores M-Pesa
credentials, PINs or card data and does not call a payment gateway.

### Data quality

`/admin/data-quality` runs read-only scans for duplicate or missing
identifiers, learner accounts without learner records, stale guardian requests,
learners without a primary guardian, overdue invoices and mobile payments
without a transaction code. Only two fixes are offered: trimming identifier
whitespace and filling a missing admission date from the record's creation
date. **Preview fix** always runs first and shows each before/after value. The
fix is applied only after an explicit hold/Enter confirmation, in one
transaction, with an audit entry per change. Nothing is deleted.

## Audit trail

`/admin/audit` shows a read-only, institution-scoped history. Each row names
the actor, action, record, time and changed fields; opening a row shows the
field-level before/after values. Platform administrators may review all
schools; other users see only their own school. Passwords and other sensitive
fields are never captured. Important actions are recorded in `core_auditlog`
(user, action, entity, IP, timestamp). Never delete audit rows or add a client
write path to this API.
