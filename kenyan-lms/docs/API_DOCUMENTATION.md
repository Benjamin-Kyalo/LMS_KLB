# API documentation

Base URL: `http://127.0.0.1:8000/api`

The frontend calls `/api` through the Vite dev proxy
(`frontend/vite.config.js`) and uses `VITE_API_BASE_URL` with `/api` as the
default. The backend allows credentialed CORS from its configured origins.

**Authentication is Django session-cookie based.** The browser receives an
HttpOnly session cookie; the CSRF cookie is readable and the frontend echoes it
as the `X-CSRFToken` header on state-changing requests. Identity and roles are
always re-read from `/api/auth/me/` (the `/auth/me/` endpoint). No bearer token
is issued at login, and no `klb_token` or `klb_user` is kept in `localStorage`.
Legacy token authentication remains only for compatibility; those tokens are
revoked on logout, password change and reset. The session expires after one hour
of inactivity (`SESSION_COOKIE_AGE=3600`, overridable to `1800` for 30 minutes);
authenticated requests refresh that window in line with
`SESSION_SAVE_EVERY_REQUEST`.

This is a **normal web app**: there is no service worker, PWA manifest or
native wrapper. By default failed mutations return an error and remain unsaved.
When `OFFLINE_MODE_ENABLED=True`, a narrow low-bandwidth mode permits cached
public reads and allowlisted theming `PATCH`/`DELETE` writes on an already-loaded
page; queued writes use `If-Match` and show 409 conflicts. Uploads still require
a live network connection. Historical references to the old broad offline queue
are superseded. See `OFFLINE_MODE_REVERSAL.md`.

The frontend keeps all HTTP calls in `frontend/src/services/api.js`.

## Which UI side uses these endpoints

Staff pages live under `/admin/...` (`DashboardLayout`); learner and guardian
pages live under `/portal/...` (`PortalLayout`). `/` is the public homepage and
old root URLs redirect by role. Examples:

| UI route | Side | Main endpoints |
|---|---|---|
| `/admin` | Staff | `/api/reports/dashboard/`, `/api/reports/analytics/` |
| `/admin/learners`, `/admin/teachers`, `/admin/guardians` | Staff | `/api/learners/`, `/api/teachers/`, `/api/guardians/` |
| `/admin/courses`, `/admin/modules`, `/admin/lessons` | Staff | `/api/courses/`, `/api/courses/modules/`, `/api/courses/lessons/` |
| `/admin/school` | Staff admin only | `/api/institutions/mine/` |
| `/admin/appearance` | `SUPER_ADMIN`, `ADMIN`, or a custom role with `admin.access` and `appearance.manage` | `/api/theming/palettes/`, `/api/theming/site-content/` |
| `/portal` | Learner / guardian | `/api/reports/my-learners/`, `/api/reports/learner/{id}/` |
| `/portal/courses`, `/portal/assignments`, `/portal/quizzes` | Learner / guardian | `/api/courses/`, `/api/courses/assignments/`, `/api/assessments/quizzes/` |
| `/library` | Public | `/api/content/facets/`, `/api/content/public/books/`, `/api/content/public/resources/` |
| `/contact` | Public | `/api/core/public-enquiries/` |
| `/portal/textbooks`, `/portal/resources`, `/portal/documents` | Learner / guardian | `/api/content/available/`, `/api/content/portal/resources/`, `/api/content/portal/documents/` |
| `/portal/reports`, `/portal/communications` | Learner / guardian | `/api/reports/learner/{id}/`, `/api/communications/announcements/` |

For create requests, omit business reference fields such as
`admission_number`, `staff_number`, `code` and `isbn` to have the server
generate them. Official supplied values are preserved and checked for
duplicates. Visible identifiers are `TR_SCHOOL_YYYY/MM_NNN` (teachers),
`LR_SCHOOL_YYYY/MM_NNN` (learners), `GD_SCHOOL_YYYY/MM_NNN` (guardians) and
`INST_YYYY_NNN` (institutions); database primary and foreign keys stay numeric.
Blank usernames are generated from a sanitized `first_last` and made unique.
The identifiers appear in the Users, Learners, Teachers and Guardians tables.
See `REFERENCE_NUMBERING.md`.

## Public / health

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | API and database status (service name `KLB Elimu`) |
| GET | `/api/core/client-config/` | Public low-bandwidth booleans, path allowlists and limits (`Cache-Control: public, max-age=300`) |
| POST | `/api/core/public-enquiries/` | Anonymous contact-form submission → real enquiry reference |
| POST | `/api/auth/login/` | Username + password → session cookie and user (CSRF cookie set) |
| POST | `/api/auth/register/` | Public self-service signup (learner, guardian or provisional teacher only) |
| POST | `/api/auth/password/reset/` | Email a reset link (console in dev) |
| POST | `/api/auth/password/reset/confirm/` | Set a new password |

### Public enquiries

`POST /api/core/public-enquiries/` is the managed `/contact` form's submission
endpoint. It uses `AllowAny` with no authentication classes, so no session,
token or learner record is needed. It is throttled by
`PUBLIC_ENQUIRY_THROTTLE_RATE` (default `10/hour` in `config.settings`) through
`PublicEnquiryThrottle`; the rate is keyed by the requester identity DRF obtains
from the request.

| Field | Required | Notes |
|---|---|---|
| `full_name` | Yes | Contact name |
| `email` | Yes | Valid email address |
| `phone` | No | Optional contact phone |
| `organisation` | No | Optional school or organisation |
| `category` | Yes | One of the options managed at `/admin/appearance` |
| `subject` | Yes | Short subject line |
| `message` | Yes | The enquiry itself |

Strings are whitespace-normalised before saving. `reference`, `status`, `id` and
`created_at` are server-controlled; unknown fields and client-supplied values
for those fields are ignored. A successful save returns HTTP 201 with a real
server-generated `ENQ` reference:

```json
{
  "reference": "<server-generated ENQ reference>",
  "message": "Your enquiry has been received. Keep your reference number for any follow-up communication."
}
```

The reference shown above is illustrative; the value comes from the reference
generator. No response time is promised. The frontend displays the managed
confirmation wording from `publicPages.contact.confirmation` alongside the
returned reference. The save and its audit entry are one transaction, so a
failed submission leaves no partial record. The `public_enquiry.received` audit
row records only the reference and category: no `full_name`, `email`, `phone`,
`organisation` or message text is written to `AuditLog`. The contact details
themselves live on the `PublicEnquiry` record, not in browser storage.

### Public registration

`POST /api/auth/register/` accepts `username`, `email`, `password`,
`first_name`, `last_name`, `role` and `institution`, plus role-specific fields.
The only accepted roles are `LEARNER`, `GUARDIAN` and `TEACHER`; any
administrator role is rejected by the serializer, not just hidden in the UI.

| Role | Additional required fields | Result |
|---|---|---|
| `LEARNER` | `date_of_birth`, `gender` | Active account and linked learner record |
| `GUARDIAN` | `relationship_to_learner` (`occupation` optional) | Active account and linked guardian record |
| `TEACHER` | `employment_type` (`PERMANENT`, `CONTRACT`, `PART_TIME` or `VOLUNTEER`) | Inactive account and teacher record until an institution `ADMIN` approves it |

A successful response is HTTP 201 with `{"detail", "user"}`. The frontend then
signs in the new learner or guardian; teacher accounts wait for approval. No
administrator role can be requested through this endpoint, and no bearer token
is issued. A signed-in user cannot open another registration: `/register` shows
an **Already signed in** state with **Sign out** and **Go to workspace**
options.

### Identity onboarding and verification

| Method | Endpoint | Purpose |
|---|---|---|
| GET, PATCH | `/api/auth/onboarding/me/` | Read or update the signed-in user's onboarding checklist; GET is also embedded in `/api/auth/me/` |
| GET | `/api/teachers/approvals/` | Pending and decided teacher approvals (institution/admin scoped) |
| POST | `/api/teachers/approvals/{id}/approve/` | Activate a teacher and optionally assign a class, subject and year |
| POST | `/api/teachers/approvals/{id}/reject/` | Reject with a required short reason |
| GET, POST | `/api/learners/link-requests/` | Guardian link requests (`GLR` reference prefix); filter by `guardian`, `learner` and `status` |
| POST | `/api/learners/link-requests/{id}/verify/` | Verify a link; creates or confirms the `LearnerGuardian` grant and accepts access flags (`can_view_academics`, `can_view_attendance`, `can_view_fees`) and `is_primary` |
| POST | `/api/learners/link-requests/{id}/reject/` | Reject a link request with a required short reason |
| GET, POST | `/api/learners/guardian-links/` | Admin-managed learner↔guardian links, created from the Learners (**Link guardian**) and Guardians (**Link learner**) modals; search options show name plus unique identifier; duplicates and cross-school links are rejected |

Teacher approval references use the `TAP` prefix. Link requests move through
`PENDING`, `VERIFIED` and `REJECTED`; the **Guardian links** page shows all three
states and lets staff decide pending requests. An institution `ADMIN` may
decide approvals or link requests; custom roles may do so only when the relevant
people capability is picked and enforced by the backend. All decisions are audit
logged. These mutations require a live connection; the narrow low-bandwidth
allowlist covers theming writes only, not people or guardian-link changes.

## Roles and capabilities

The built-in roles are `SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER`
and `GUARDIAN`.

- `SUPER_ADMIN` is global and unrestricted, including institution management
  and granting any role. It is unchanged by the role simplification.
- `ADMIN` has unrestricted CRUD inside its own institution. It can create and
  assign custom roles, but cannot grant `SUPER_ADMIN` or create global
  institutions.
- `CUSTOM` is a named, reusable role identified by a `custom_role` id and made
  up of picked capabilities. It enters the admin portal only when
  `admin.access` is selected; the backend enforces all other capabilities.
- `TEACHER`, `LEARNER` and `GUARDIAN` keep their existing scope.

The retired names `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and
`CONTENT_MANAGER` are removed. Existing accounts with those roles are migrated
to `ADMIN`; `SUPER_ADMIN` accounts are unchanged. The migration changes only
the role value: passwords are never changed, generated, printed or placed in
documentation. Verify the `institution` on migrated accounts, since a user with
no institution sees no institution data by design.

The custom-role capability allowlist is:
`admin.access`, `users.manage`, `roles.manage`, `academics.manage`,
`learners.manage`, `teachers.manage`, `guardians.manage`, `courses.manage`,
`assessments.manage`, `content.manage`, `attendance.manage`, `fees.manage`,
`communications.manage`, `reports.view`, `appearance.manage`,
`institutions.manage`, `tutor.use`.

## Authentication and users

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/logout/` | End the Django session; revoke any legacy token |
| GET, PATCH | `/api/auth/me/` | Re-read identity/roles and read or update own profile. GET includes `institution_name`, `institution_logo` (absolute URL or `null`), `custom_role`, `custom_role_name` and `capabilities` |
| POST | `/api/auth/password/change/` | Change own password |
| GET, POST | `/api/auth/users/` | List / create users (admin only to create) |
| GET | `/api/auth/users/roles/` | Available options: built-in roles plus named custom roles |
| GET, POST | `/api/auth/roles/` | List / create custom roles (custom-role CRUD) |
| GET, PATCH, DELETE | `/api/auth/roles/{id}/` | Read / update / delete a custom role |
| POST | `/api/auth/users/{id}/set_active/` | Activate / deactivate |
| POST | `/api/auth/users/{id}/reset_password/` | Admin-initiated password reset (needs `users.manage`; not for your own account) |
| GET, POST | `/api/auth/admin-invitations/` | List / issue administrator invitations (`SUPER_ADMIN` or `ADMIN`) |
| GET, PATCH, DELETE | `/api/auth/admin-invitations/{id}/` | Inspect, update or revoke an invitation. DELETE sets `revoked=true` |
| POST | `/api/auth/admin-invitations/accept/` | Public redemption of a valid invitation token; creates the session and returns the user |

Create a custom-role user by sending the role kind and the chosen role id:

```json
{ "username": "librarian1", "role": "CUSTOM", "custom_role": 12 }
```

User responses echo `role`, `custom_role`, `custom_role_name` and the effective
`capabilities` list alongside the usual profile fields. A custom role cannot be
used to grant `SUPER_ADMIN`, and a role without `admin.access` does not enter
the admin portal. Custom-role CRUD is guarded by the `roles.manage` capability
and by the same institution scoping as other admin data.

`reset_password` generates a valid temporary password, returns it once in the
response, sets `must_change_password`, invalidates the user's existing sessions
and writes a `password_reset` audit entry. The login response carries
`must_change_password`, and the frontend sends the user to the profile page to
choose a new password. Users who forget a password can use the login page's
**Forgot your password?** link and the `/reset-password` route.

Administrator invitations are the only way to create an administrator through
the application. The issuing admin supplies `email`, `role` and, for institution
roles, `institution`. The server generates `token`, `expires_at`, `accepted_at`,
`revoked` and `created_at`. `ADMIN` cannot invite into another institution or
grant `SUPER_ADMIN`; only `SUPER_ADMIN` may grant any role. Tokens are
high-entropy, single-use and expire after seven days. They are stored in the
database so an authorised admin can copy them later, are **not** HMAC-signed or
hashed, and must be treated like credentials.

To redeem an invitation, post `token`, `username`, `email`, `first_name`,
`last_name` and `password` to the `accept/` endpoint. The email must match the
invitation. The role and institution come from the token and cannot be chosen
in the request. The form's confirmation field is checked in the browser and is
not sent to the API. The frontend route is `/admin/signup?token=...`; it is not
advertised in public navigation or public registration.

Password hashing remains PBKDF2. Login failures are counted in the database
for IP/username and username-only scopes, with DRF throttles on login,
registration, reset, tutor and KEMIS endpoints. `X-Forwarded-For` is trusted
only from configured proxy IPs. Reset links expire after one hour and use
hashed, single-use records; a successful password change or reset invalidates
active sessions and legacy tokens. See `SECURITY_AUDIT.md`.

## SIS

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/institutions/` | Institutions (create/delete: `SUPER_ADMIN` only) |
| GET, PATCH | `/api/institutions/mine/` | Read or edit the signed-in user's own school. PATCH is limited to `SUPER_ADMIN` and `ADMIN`; custom roles are limited to their picked capabilities; learners and guardians get HTTP 403 |
| GET, POST | `/api/institutions/types/` | Institution types |
| GET, POST | `/api/institutions/academic-years/` | Academic years |
| GET, POST | `/api/institutions/terms/` | Terms |
| GET, POST | `/api/institutions/classes/` | Classes |
| GET, POST | `/api/institutions/subjects/` | Subjects |
| GET, POST | `/api/learners/` | Learners |
| POST | `/api/learners/bulk-import/` | CSV import |
| GET | `/api/learners/{id}/guardians/` | Linked guardians |
| GET, POST | `/api/learners/guardian-links/` | Admin-managed guardian links (scoped through the learner); managed from both Learners and Guardians |
| GET, POST | `/api/teachers/` | Teachers |
| GET, POST | `/api/guardians/` | Guardians |
| GET, POST | `/api/attendance/` | Attendance records |
| POST | `/api/attendance/bulk/` | Bulk marking |
| GET, POST | `/api/academics/timetable/` | Timetable entries |
| GET, POST | `/api/academics/events/` | School events |

## LMS and assessment

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/courses/` | Courses |
| GET, POST | `/api/courses/modules/` | Modules |
| GET, POST | `/api/courses/lessons/` | Lessons |
| GET, POST | `/api/courses/assignments/` | Assignments; `rubric`, `allow_resubmission` and `max_attempts` select the marking grid |
| POST | `/api/courses/progress/mark-complete/` | Idempotent progress update |
| GET, POST | `/api/courses/submissions/` | Submissions; staff see all in-scope rows, learners see their own, permitted guardians see linked learners |
| POST | `/api/courses/submissions/{id}/grade/` | Grade a submission with a direct score |
| POST | `/api/courses/submissions/{id}/grade-rubric/` | Score every selected criterion; the server totals marks and resolves the percentage band |
| POST | `/api/courses/submissions/{id}/publish-feedback/` | Publish grade and feedback to the learner and permitted guardians |
| POST | `/api/courses/submissions/{id}/resubmit/` | Learner-only new attempt; keeps the earlier answer and grade in history |
| GET, POST | `/api/assessments/questions/` | Question bank |
| GET, POST | `/api/assessments/quizzes/` | Quizzes |
| GET, POST | `/api/assessments/attempts/` | Quiz attempts |
| POST | `/api/assessments/attempts/submit/` | Auto-mark objective answers |
| GET, POST | `/api/assessments/exams/` | Exams |
| GET, POST | `/api/assessments/results/` | Exam results |

## Curriculum and publishing

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/curriculum/frameworks/` | Versioned frameworks |
| GET, POST | `/api/curriculum/levels/` | Education levels |
| GET, POST | `/api/curriculum/learning-areas/` | Learning areas |
| GET, POST | `/api/curriculum/strands/` | Strands |
| GET, POST | `/api/curriculum/sub-strands/` | Sub-strands |
| GET, POST | `/api/curriculum/outcomes/` | Learning outcomes |
| GET, POST | `/api/curriculum/competencies/` | Competencies |
| GET, POST | `/api/curriculum/rubrics/` | Rubrics with nested achievement bands and criteria |
| GET, POST | `/api/curriculum/rubric-levels/` | Percentage achievement bands (staff write; global templates platform-only) |
| GET, POST | `/api/curriculum/rubric-criteria/` | Scored criteria used by the marking grid |
| GET, POST | `/api/curriculum/feedback-comments/` | Reusable feedback phrase bank |
| GET, POST | `/api/curriculum/evidence/` | Competency evidence |
| GET, POST | `/api/content/textbooks/` | Textbook catalogue |
| POST | `/api/content/textbooks/{id}/publish/` | Publish a title |
| GET | `/api/content/available/` | Titles licensed to your institution |
| GET, POST | `/api/content/chapters/` | Chapters |
| GET, POST | `/api/content/resources/` | Admin-managed resource records (taxonomy, uploads, links, embeds) |
| GET | `/api/content/resources/{id}/download/` | Permission-checked attachment download |
| GET | `/api/content/exercises/` | Chapter exercises |
| GET, POST | `/api/content/exercise-attempts/` | Exercise attempts |
| GET, POST | `/api/content/access/` | Licence grants |

### Rubric marking rules

`POST /api/courses/submissions/{id}/grade-rubric/` accepts
`{"criteria": [{"criterion": id, "score": "4.00", "comment": "..."}], "overall_feedback": "...",
"private_notes": "..."}`. The server rejects criteria outside the assignment's rubric, duplicate
criteria, scores above a criterion's maximum, and totals above the assignment maximum. Each attempt's
criterion scores are snapshotted with the criterion name and limit, so later rubric edits cannot alter
an existing grade. The final percentage is mapped to a `RubricLevel` band; bands are expressed as
percentages from `0` to `100`, not raw rubric points.

Grades and written feedback are private until `publish-feedback/` is called. That action notifies the
learner and verified guardians with `can_view_academics`; `private_notes` never leaves staff views.
`resubmit/` accepts `text_answer`, an `attachment`, or both, and is restricted to the learner who owns
the submission while attempts remain. Rubric build and grading actions write `rubric.*` and
`submission.*` audit entries; see `RUBRICS_MASTERY.md`.

### Resource discovery (Phase 2)

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/content/facets/` | Public | Levels, learning areas, collections, types; adds subjects and classes for signed-in readers |
| GET | `/api/content/public/books/` | Public | Published, non-expired book metadata with `cover_url` and licence label |
| GET | `/api/content/public/resources/` | Public | Published, public-scope resources with `thumbnail_url` |
| GET | `/api/content/portal/resources/` | Authenticated | Published public/institution/class resources visible to the reader |
| GET | `/api/content/portal/documents/` | Authenticated | Same scoping, limited to PDF and link documents |
| GET, POST | `/api/content/collections/` | Authenticated; curator writes | Admin-managed browsing collections |
| GET, POST | `/api/content/embed-providers/` | Authenticated; curator writes | Active YouTube/Vimeo host allowlist |

Catalogue endpoints are paginated and accept `page`, `page_size`, `ordering`,
`q` (also accepted as `keyword` or `search`), and the filters advertised by each view (for example
`education_level`, `learning_area`, `collection`, `subject`, `school_class`,
`resource_type`, `delivery` and `access_scope`). Portal scoping uses the user's
institution, verified learner links, learner class or teacher assignments; it
never grants cross-school access. Public and portal serializers expose only safe
read fields and a server-built `embed_url` or scoped `download_url`. Books expose
`cover_url`; resources expose `thumbnail_url`. Both are either local frontend
artwork paths under `/images/` or uploaded files under `MEDIA_URL`, never raw
storage names or unsafe external hotlinks. The management resource endpoint also
accepts a validated `thumbnail_image` upload so curators can replace card art.
See `docs/ASSET_CREDITS.md` for OER metadata and artwork provenance.

`ContentResource` supports `delivery` values `UPLOAD`, `LINK` and `EMBED`, and
`access_scope` values `PUBLIC`, `INSTITUTION` and `CLASS`. Local file uploads are
stored under `content/resources/`. Uploads require a live connection and are
never queued for replay. Filenames and bytes are validated by magic-byte
sniffing, not by extension alone. Embed records store only a validated provider and source URL. The server checks
HTTPS, the active provider's host, and a known video ID before building a
sandboxed iframe URL; client-supplied iframe, script or HTML is never rendered.
The default maximum upload size is 5 MB (`CONTENT_RESOURCE_MAX_UPLOAD_BYTES`).
The general `/api/content/resources/` endpoint is an authenticated management
catalogue and does not apply the public/portal status gate; use the scoped
catalogue endpoints for readers. Serving private media in production still needs
an explicit web-server or object-storage decision; Django's `DEBUG` media
serving is not a deployment plan.

## Communication and reports

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/communications/announcements/` | Announcements |
| POST | `/api/communications/announcements/{id}/publish/` | Publish |
| GET | `/api/communications/notifications/` | Own notifications |
| GET | `/api/communications/notifications/unread-count/` | `{ "count": n }` for the signed-in user |
| POST | `/api/communications/notifications/{id}/mark-read/` | Mark one notification read |
| POST | `/api/communications/notifications/mark-all-read/` | Mark own notifications read |
| GET, POST, PATCH | `/api/communications/preferences/` | Own `in_app`, `email`, `sms` and `types` preferences |
| GET, POST | `/api/communications/messages/` | Direct messages |
| GET | `/api/reports/dashboard/` | School dashboard figures (staff only) |
| GET | `/api/reports/analytics/` | Chart-ready attendance, exam and learner status data (staff only) |
| GET | `/api/reports/my-learners/` | Learners the caller may open (for report pickers and portal home) |
| GET | `/api/reports/learner/{id}/` | Learner report (scoped by institution, link and guardian permissions) |
| GET, POST | `/api/reports/snapshots/` | Saved reports |

## Cross-system workflows

These endpoints reuse the shared notification, audit and fee-ledger records.
They do not introduce a second inbox, audit store or receipt model.

### Early warning

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/analytics/early-warning/` | Risk alerts, exact signals, rule descriptions and summary for the caller's school |
| POST | `/api/analytics/early-warning/refresh/` | Recalculate and create intervention tasks for medium/high learners without an open task |
| GET | `/api/analytics/interventions/` | Intervention tasks for the caller's school |
| POST | `/api/analytics/interventions/{id}/assign/` | Assign with `{ "user_id": n }` from the same institution |
| POST | `/api/analytics/interventions/{id}/complete/` | Mark completed |
| POST | `/api/analytics/interventions/{id}/dismiss/` | Dismiss without deleting evidence |

Rules are additive: attendance 3, assessment 3, submission 2, progress 2 and
fees 1 point. Levels are `HIGH` at 6+, `MEDIUM` at 3–5, `LOW` at 1–2 and `NONE`
at zero. The report response includes a `rules` object whose descriptions are
safe to show to staff and families.

### Mastery badges

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/analytics/mastery/` | Derived badge displays for the caller's institution (staff only) |
| GET | `/api/analytics/my-mastery/` | The signed-in learner's own derived badges |

Staff may filter the school report with `learner`, `competency` and
`mastery_level`. Badge bands use the shared 0–1 mastery scores: `BEGINNING`
0.25, `DEVELOPING` 0.50, `ACHIEVING` 0.75 and `EXTENDING` 1.00. Only the top two
bands are marked earned. These are read-only calculations from
`CompetencyEvidence`; no award or badge record is created.

### Fee ledger and receipts

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/fees/invoices/summary/` | Invoice count and billed, recorded and outstanding totals |
| GET | `/api/fees/reconciliation/` | `{ "exceptions": [...], "counts": {...} }` for mobile payments needing office review |
| GET | `/api/fees/payments/{id}/receipt/` | Printable receipt data derived from the payment |
| POST | `/api/fees/payments/{id}/reconcile/` | Confirm a transaction code and clear the exception |

`POST` reconciliation accepts `{ "transaction_reference": "CODE", "notes": "..." }`.
Mobile payments require a code; the same code cannot be used twice in one
school. Cash, bank and other methods are considered reconciled when recorded.
The app has no M-Pesa credentials, PINs, card fields or live gateway calls.

### Data quality and audit

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/core/data-quality/?institution=<id>` | Read-only issue counts and samples |
| POST | `/api/core/data-quality/fix/` | Preview by default; apply with `confirm: true` |
| GET | `/api/core/audit/` | Read-only, institution-scoped history |

The fix body uses `{ "issue_type": "identifier_whitespace" }` for preview and
adds `"confirm": true` to apply. Only `identifier_whitespace` and
`learner_admitted_date` are allowlisted. Applied fixes are transactional and
audited; no record is deleted. `GET /api/core/audit/` accepts `action`,
`entity_type`, `entity_id`, `user`, `search` and `ordering`. Platform
administrators may pass `institution=<id>` to the data-quality scan; other
administrators are silently scoped to their own school.

### Public enquiry review queue

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/core/enquiries/` | `SUPER_ADMIN` only | Platform-admin review queue for public enquiries |
| GET | `/api/core/enquiries/{id}/` | `SUPER_ADMIN` only | Inspect one enquiry |
| PATCH | `/api/core/enquiries/{id}/` | `SUPER_ADMIN` only | Change the workflow status |

The viewset is restricted by `IsSuperAdmin`: anonymous callers receive 401 and
institution `ADMIN` accounts receive 403. Institution-scoped staff and custom
roles have no access to this queue; no admin screen is provided for it, so
review uses this API. Records are ordered newest first and support filters on
`status` and `category`, search on `reference`, `full_name`, `email`,
`organisation` and `subject`, and ordering by `created_at` or `subject`.

Only `status` is writable, with values `NEW`, `IN_REVIEW` and `RESOLVED`.
Reference, contact fields, category, subject, message and timestamps are
read-only. Every successful update writes a `public_enquiry.status_changed`
audit entry containing the reference and new status; the actor is the platform
administrator making the change. Submission itself writes only the non-PII
`public_enquiry.received` details described above.

## Interoperability and governed AI

These endpoints use a separate, narrowly configured auth surface. Ordinary
session cookies are not accepted by the OneRoster views, and no bearer token is
issued by `/api/auth/login/`.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/integration/oneroster/v1p1/courses/` | HS256 assertion with `courses.read` | Published courses in the pinned institution |
| GET | `/api/integration/oneroster/v1p1/classes/` | HS256 assertion with `classes.read` | Published courses shaped as classes |
| GET | `/api/integration/oneroster/v1p1/users/` | HS256 assertion with `users.read` | Active learners and teachers in the pinned institution |
| GET | `/api/integration/oneroster/v1p1/enrollments/` | HS256 assertion with `enrollments.read` | Derived teacher/learner memberships |
| GET | `/api/integration/oneroster/v1p1/orgs/` | HS256 assertion with `orgs.read` | The pinned institution |
| GET, POST | `/api/integration/lti/launch/`, `/api/integration/oidc/`, `/api/integration/jwks/`, `/api/integration/oauth/token/` | Public, throttled | Generic 403: deliberately unsupported |
| GET | `/api/tutor/conversations/health/` | Authenticated | Provider and safe `policy` metadata |

Clients are configured only through `KLB_ONEROSTER_CLIENTS`; assertions are
short-lived HS256 JWTs checked with stdlib HMAC. Wrong algorithms, expired or
over-long assertions, unknown clients and wrong audiences return a generic 401.
Successful reads write `integration.oneroster.read` audit rows without secrets
or personal payloads. Tutor ask responses include `policy`, and each ask writes
institution-scoped `tutor.answer.requested` and `tutor.answer.generated` audit
rows whose details exclude the question, answer and any secret. See
`INTEROPERABILITY_AI.md`.

## School profile and logo upload

`GET /api/institutions/mine/` returns the caller's institution only. The
profile fields include `name`, `code`, `institution_type_name`, `county`,
`phone`, `email`, `website`, `motto`, `address_line` and `logo` (a URL). The
staff page `/admin/school` uses PATCH on the same endpoint.

To change the logo, send a multipart PATCH with the form field `logo`:

```text
PATCH /api/institutions/mine/
Content-Type: multipart/form-data

logo=<image file>
```

Accepted types are JPG (`image/jpeg`), PNG (`image/png`) and WebP
(`image/webp`), with a maximum size of 2 MB. Other types and larger files
return HTTP 400 with a field error. Files are stored under
`institutions/logos/`. The frontend calls `api.upload()` from
`frontend/src/services/api.js`, which needs a live connection; a failed upload
surfaces an error and remains unsaved. After a successful save, the UI refreshes
`/api/auth/me/` so both layouts show the new logo.

The migration behind these fields is
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`.
A backup was taken first at `backups/lms_20261123_134452.sql`.

## Theming and site content

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/theming/active/` | Public | Active palette with ramp shades |
| GET, POST | `/api/theming/palettes/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Palette catalogue and onboarding |
| POST | `/api/theming/palettes/{id}/activate/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Choose one active palette |
| GET | `/api/theming/site-content/` | Public | Merged wording, photos and section styles |
| PATCH | `/api/theming/site-content/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Validate and save edited wording or section styles |
| POST | `/api/theming/site-content/image/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Upload and publish one allowlisted photo slot |
| DELETE | `/api/theming/site-content/image/{slot}/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Clear one managed photo slot |
| POST | `/api/theming/site-content/image/{slot}/reset/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Restore one slot to its shipped default |
| POST | `/api/theming/site-content/hero-image/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Legacy alias that uploads the homepage hero slot |

As of 25 November 2026, eight built-in palettes are seeded: Ocean Blue
Serenity, Sage Green, Blue Coral Daylight, Forest Green, Citrus Bloom, Heritage
Spice, Bright Horizon and Plum Harvest. Plum Harvest (`plum-harvest`, from
`color 7.png`) is the current active palette and the fresh-install default;
`theming.0004_seed_and_activate_plum_harvest` applied that selection locally.
All eight are available for activation without changing component code.

A site content PATCH accepts `{ "content": { ... } }` or a bare content object.
Only known sections and keys are kept. Links must be local paths such as
`/library` or full HTTPS addresses. Script, data and protocol-relative links are
rejected with a field error such as `header.signInHref`. Omitted fields keep
their saved value, and every successful save writes a `site_content.updated`
audit entry. Section styles accept only six-digit hex colours and the supplied
corner and spacing choices; there is no raw CSS field. A background and text
colour pair must reach 4.5:1 contrast.

Managed photo uploads accept a multipart field named `image` (or `file`) plus a
`slot` chosen from `hero`, `workspace-learning`, `workspace-school`,
`workspace-publishing`, `insights`, `login`, `register` and `tutor`. JPG, PNG and
WebP files at least 640×360 px and at most 5 MB are checked by extension, bytes
and decoded image before being stored under `MEDIA_ROOT/site-content/<slot>/`.
A successful upload updates only that slot, returns the published content and
writes a `site_content.image_uploaded` audit entry. `DELETE` clears the slot and
writes `site_content.image_removed`; `POST .../reset/` restores the shipped
value and writes `site_content.image_reset`. Empty image values are valid; other
content values still go through the normal link validation. `SUPER_ADMIN` and
`ADMIN` can manage photos, wording and section styles; a custom role can do so
only when `admin.access` and `appearance.manage` are selected and enforced by
the backend.

The frontend reads the same endpoint through `SiteContentContext` and merges
the live response over the local defaults in
`frontend/src/config/publicSite.js`. Administrators manage colours, photos,
wording and section styles from the single `/admin/appearance` page.
`/admin/theme` and `/admin/site-content` remain aliases that open the matching
tab. By default there is no offline content cache: if the API is unreachable, the
page shows an error or the built-in defaults, and a failed save remains unsaved.
If low-bandwidth mode is explicitly enabled, only the public allowlisted reads
and theming writes in `OFFLINE_MODE_REVERSAL.md` may use device storage; retired
cards never return through a cached response. See `docs/PUBLIC_SITE_CONTENT.md`. The retired public-site `content` / “Content
managers” cards stay retired; a cached override cannot bring them back. Only
the learner, guardian and teacher role cards are supported.

## Response conventions

- List endpoints are paginated: `{"count", "next", "previous", "results"}`.
  Use `listAll()` in the frontend to flatten them.
- Validation errors return HTTP 400 with a professional field-prefixed message
  such as `email: This field may not be blank.`; the frontend shows the message
  and never renders raw JSON.
- Opt-in theming writes may send `If-Match` with the loaded `updated_at`. A
  stale value returns HTTP 409 with `code`, `message` and a safe `server` copy
  for deliberate review; the frontend never silently overwrites it.
- Cross-institution detail requests return 404, not 403.
- Content, assessment, course, learner, fee and attendance reads are scoped
  server-side; ordinary users receive reduced field sets.
- Health-check database failures return a generic `Database unavailable`
  response; details go to logs.
- Authenticated `/api/` responses carry `Cache-Control: no-store` and security
  headers; production adds a CSP.
- Timestamps are timezone-aware (`Africa/Nairobi`).
