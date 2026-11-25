# User roles, permissions and journeys

Status: **Current-state role model**, aligned to `docs/PRODUCT_DIRECTION.md`,
`docs/ADMIN_ACCESS.md` and `docs/API_DOCUMENTATION.md`. Dated decisions below are
retained as history; where they name retired roles, this section supersedes them.

**Current direction:** normal web app only. The offline queue, sync/conflict UI,
service worker, PWA manifest and native wrapper are removed. Failed mutations
show an error and remain unsaved, and uploads require a live connection.
Authentication uses Django session cookies; identity/roles are re-read from
`/api/auth/me/`. See `README.md` and `SECURITY_AUDIT.md`.

## Role taxonomy

The simplified model has six built-in role kinds plus reusable named custom
roles. There is no longer a platform/school/institution administrator hierarchy
or a separate content-manager role.

| Category | System role(s) | Access side | Notes |
|---|---|---|---|
| Administrator (global) | `SUPER_ADMIN` | `/admin` | Global unrestricted access, including institution management and granting any role. Unchanged by the simplification |
| Administrator (institution) | `ADMIN` | `/admin` | Unrestricted CRUD within its own institution; can create and assign custom roles; cannot grant `SUPER_ADMIN` or create global institutions |
| Custom role | `CUSTOM` with a `custom_role` id | `/admin` **only** when `admin.access` is picked | Named, reusable role carrying only the selected capabilities; the backend enforces every capability |
| Teacher | `TEACHER` | `/admin` | Teacher accounts are inactive until an administrator approves them |
| Student / Learner | `LEARNER` | `/portal` | Own records only |
| Guardian / Parent | `GUARDIAN` | `/portal` | Linked learners only |

**Retired names and migration.** `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`,
`SCHOOL_ADMIN` and `CONTENT_MANAGER` are removed. Existing accounts with any of
those values are migrated to `ADMIN`; `SUPER_ADMIN` accounts are unchanged. The
migration changes only the role value — passwords are never changed, generated,
printed or included in documentation. Check the institution on migrated
accounts: a user with no institution sees no institution data by design.

**Historical decision — 24 November 2026 (superseded):** one primary
`SUPER_ADMIN` had complete control and delegated platform/school administrators
were issued through expiring, single-use invitations. That delegated hierarchy
has been replaced by the `ADMIN` and `CUSTOM` model above. Invitations remain
expiring and single-use, and admin accounts still cannot be created through
public registration.

### Capabilities

Custom roles pick from this allowlist. Selecting `admin.access` is what lets the
role enter the admin portal; the other capabilities are enforced by the backend,
not merely hidden in the UI.

`admin.access`, `users.manage`, `roles.manage`, `academics.manage`,
`learners.manage`, `teachers.manage`, `guardians.manage`, `courses.manage`,
`assessments.manage`, `content.manage`, `attendance.manage`, `fees.manage`,
`communications.manage`, `reports.view`, `appearance.manage`,
`institutions.manage`, `tutor.use`.

Custom roles are created, read, updated and deleted through
`/api/auth/roles/`; `/api/auth/users/roles/` returns the built-ins plus custom
options. User payloads use `{ "role": "CUSTOM", "custom_role": <id> }`, and user
responses include `custom_role`, `custom_role_name` and `capabilities`.

## Permission principles

1. The backend is authoritative; frontend guards only shape the UI, and every
   custom-role capability is enforced server-side.
2. Public registration can create only `LEARNER`, `TEACHER` and `GUARDIAN`.
3. Admin accounts come from `SUPER_ADMIN` or `ADMIN` through an expiring,
   single-use, server-side invitation. `ADMIN` cannot grant `SUPER_ADMIN`.
4. Role changes cannot grant `SUPER_ADMIN` unless the actor is `SUPER_ADMIN`.
5. Institution-scoped users see only their institution and linked records;
   `SUPER_ADMIN` is the only global scope.
6. Guardians see only learners explicitly linked to them.
7. Teachers see assigned classes/learners, not every learner in the institution
   unless explicitly granted.
8. Learners see their own data and resources for their class/level/subject.
9. Roles come from the server on every identity read (`/api/auth/me/`); the
   browser keeps no `klb_token`/`klb_user` credentials, only the session and
   CSRF cookies.

## Permission matrix

Legend: **F** full (global for `SUPER_ADMIN`, institution-wide for `ADMIN`),
**R** read only, **M** manage assigned records, **—** no access. A capability
name means a custom role gets that area only when the capability is selected;
`admin.access` is required before the role appears in `/admin` at all.

| Area | `SUPER_ADMIN` | `ADMIN` | `CUSTOM` (only when picked) | Teacher | Learner | Guardian |
|---|---|---|---|---|---|---|
| Public site content | F | F | `appearance.manage` | — | — | — |
| Users and roles | F | F; create/assign custom roles, never `SUPER_ADMIN` | `users.manage`, `roles.manage` | — | Own profile | Own profile |
| Academic structure | F | F | `academics.manage` | R assigned | R own | R linked |
| Learning resources | F | F | `content.manage` | M assigned | R allowed | R linked |
| Assignments/assessments | F | F | `assessments.manage` | M assigned | R/submit own | R linked |
| Attendance/progress | F | F | `attendance.manage`, `reports.view` | M assigned | R own | R linked |
| Messages/announcements | F | F | `communications.manage` | M assigned | R targeted | R targeted |
| Reports | F | F within institution | `reports.view` | R assigned | R own | R linked |
| Branding/theme | F | F | `appearance.manage` | — | — | — |
| Institutions | F (create/delete global) | Read/edit own institution only; no global creation | `institutions.manage` | — | R own identity | R own identity |
| System settings | F | — | — | — | — | — |
| Audit logs | F | R own institution | `reports.view` | — | — | — |

## Registration journeys

Field sets below are confirmed for Phase 1: keep the current serializer fields
and add only the minimum role-specific extras shown here. Any additional field
needs a separate requirement.

### 1. Public visitor

1. Arrives at `/` and sees a short explanation, catalogue/resource entry and
   sign-in/register actions.
2. Can browse public catalogue, documents and announcements without an account.
3. Chooses **Register** and identifies as Student, Teacher or Guardian.
4. After registration, is routed to the correct onboarding state.

### 2. Learner

**Fields:** full name, date of birth or level, school/class where known, contact
email or phone, preferred language, guardian contact where available.

**Flow:** self-register → email/phone validation → account active or pending
school confirmation → profile completion → `/portal` learner dashboard.

**First dashboard:** my subjects, my resources, work due, recent results,
announcements, profile completeness.

### 3. Teacher

**Fields:** full name, school/institution, subjects, level/classes, phone,
email, professional notes.

**Flow:** self-register → account created inactive → an institution `ADMIN`
approves and assigns classes → teacher signs in → onboarding checklist →
`/admin` teacher dashboard.

**First dashboard:** assigned classes, learner count, resources to prepare,
assignments due, messages, profile.

### 4. Guardian

**Fields:** full name, relationship, phone, email, preferred language, learner
identifier or linking request.

**Flow:** self-register → learner link proposed → admin/verification confirms
link → guardian signs in → `/portal` guardian dashboard.

**First dashboard:** linked learners, recent progress, upcoming work, school
announcements, messages.

**Empty state:** “No learner is linked to this account yet. Ask the school to
link you, or provide a learner code.”

### 5. Administrator

**Flow:** `SUPER_ADMIN` exists at installation → an authorised administrator
(`SUPER_ADMIN` or `ADMIN`) creates an invitation with role and institution →
invitee opens expiring single-use signup link → account created with the fixed
role → `/admin`. `ADMIN` can assign `ADMIN`, `TEACHER`, `LEARNER`, `GUARDIAN` or
a custom role, but never `SUPER_ADMIN`; only `SUPER_ADMIN` can grant that role or
create global institutions. Custom roles are created and edited through
`/api/auth/roles/`.

No public route offers administrator registration. Account creation and role
migration never generate, print or store a plain-text password for someone else.

## Daily journeys

### Administrator

- Review pending teacher approvals and guardian links.
- Manage users, custom roles, classes, subjects and academic years.
- Add/edit resources and public content.
- Publish announcements; review messages and reports.
- Change branding or active palette.
- Review audit log and system health (there is no queue/sync health view).

### Teacher

- Open assigned class and learner list.
- Add or update learning materials.
- Set assignments/assessments and record progress.
- Message learners or guardians within assigned scope.
- Review their profile and responsibilities.

### Learner

- Open dashboard and see work due.
- Find a resource by subject or class.
- Read/view resource or open assignment.
- Check progress and feedback.
- Update own profile.

### Guardian

- Select a linked learner.
- Review progress, attendance and reports.
- Read targeted announcements.
- Reply to or read school communication.
- Update own contact details.

## Onboarding checklist ownership

| Role | Checklist stored where | Completed when |
|---|---|---|
| Learner | User profile / onboarding record | Profile complete and class/level set |
| Teacher | User profile + approval record | Approved, assigned at least one class, profile complete |
| Guardian | Guardian link record | At least one learner verified, contact details complete |
| Admin | Invitation + user record | Invitation accepted and profile complete |

## Required empty and error states

- No linked learner for guardian.
- No assigned classes for teacher.
- No resources for a subject/class/level.
- No results or attendance yet.
- No pending approvals for admin.
- No search matches in catalogue or managed lists.
- Permission denied with a plain-language explanation and a safe route home.

Each state must offer a next action where one exists, and must never expose
another user's data.
