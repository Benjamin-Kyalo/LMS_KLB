# API documentation

Base URL: `http://127.0.0.1:8000/api`
Authentication: `Authorization: Token <token>` (except login, health and
password reset endpoints).

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
| `/portal` | Learner / guardian | `/api/reports/my-learners/`, `/api/reports/learner/{id}/` |
| `/portal/courses`, `/portal/assignments`, `/portal/quizzes` | Learner / guardian | `/api/courses/`, `/api/courses/assignments/`, `/api/assessments/quizzes/` |
| `/portal/textbooks`, `/portal/resources` | Learner / guardian | `/api/content/available/`, `/api/content/resources/` |
| `/portal/reports`, `/portal/communications` | Learner / guardian | `/api/reports/learner/{id}/`, `/api/communications/announcements/` |

For create requests, omit business reference fields such as
`admission_number`, `staff_number`, `code` and `isbn` to have the server
generate them. Official supplied values are preserved and checked for
duplicates. See `REFERENCE_NUMBERING.md`.

## Public / health

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | API and database status |
| POST | `/api/auth/login/` | Username + password → token and user |
| POST | `/api/auth/register/` | Public self-service signup (learner, guardian or provisional teacher only) |
| POST | `/api/auth/password/reset/` | Email a reset link (console in dev) |
| POST | `/api/auth/password/reset/confirm/` | Set a new password |

### Public registration

`POST /api/auth/register/` accepts `username`, `email`, `password`,
`first_name`, `last_name`, `role` and `institution`, plus role-specific fields.
The only accepted roles are `LEARNER`, `GUARDIAN` and `TEACHER`; any
administrator role is rejected by the serializer, not just hidden in the UI.

| Role | Additional required fields | Result |
|---|---|---|
| `LEARNER` | `date_of_birth`, `gender` | Active account and linked learner record |
| `GUARDIAN` | `relationship_to_learner` (`occupation` optional) | Active account and linked guardian record |
| `TEACHER` | `employment_type` (`PERMANENT`, `CONTRACT`, `PART_TIME` or `VOLUNTEER`) | Inactive account and teacher record until a school administrator approves it |

A successful response is HTTP 201 with `{"detail", "user"}`. The frontend then
signs in the new learner or guardian; teacher accounts wait for approval. No
token or administrator role can be requested through this endpoint.

## Authentication and users

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/logout/` | Delete current token |
| GET, PATCH | `/api/auth/me/` | Read or update own profile. GET includes `institution_name` and `institution_logo` (absolute URL or `null`) |
| POST | `/api/auth/password/change/` | Change own password |
| GET, POST | `/api/auth/users/` | List / create users (admin only to create) |
| GET | `/api/auth/users/roles/` | Available role codes |
| POST | `/api/auth/users/{id}/set_active/` | Activate / deactivate |
| GET, POST | `/api/auth/admin-invitations/` | List / issue administrator invitations (institution or platform admin) |
| GET, PATCH, DELETE | `/api/auth/admin-invitations/{id}/` | Inspect, update or revoke an invitation. DELETE sets `revoked=true` |
| POST | `/api/auth/admin-invitations/accept/` | Public redemption of a valid invitation token; returns an auth token and user |

Administrator invitations are the only way to create an administrator through
the application. The issuing admin supplies `email`, `role` and, for school or
institution roles, `institution`. The server generates `token`, `expires_at`,
`accepted_at`, `revoked` and `created_at`. A school admin cannot invite a role
above their own, and platform-only roles require a platform admin. Tokens are
high-entropy, single-use and expire after seven days. They are stored in the
database so an authorised admin can copy them later, are **not** HMAC-signed or
hashed, and must be treated like credentials.

To redeem an invitation, post `token`, `username`, `email`, `first_name`,
`last_name` and `password` to the `accept/` endpoint. The email must match the
invitation. The role and institution come from the token and cannot be chosen
in the request. The form's confirmation field is checked in the browser and is
not sent to the API. The frontend route is `/admin/signup?token=...`; it is not
advertised in public navigation or public registration.

## SIS

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/institutions/` | Institutions (create/delete: platform admins only) |
| GET, PATCH | `/api/institutions/mine/` | Read or edit the signed-in user's own school. PATCH is limited to platform and institution/school admins; learners and guardians get HTTP 403 |
| GET, POST | `/api/institutions/types/` | Institution types |
| GET, POST | `/api/institutions/academic-years/` | Academic years |
| GET, POST | `/api/institutions/terms/` | Terms |
| GET, POST | `/api/institutions/classes/` | Classes |
| GET, POST | `/api/institutions/subjects/` | Subjects |
| GET, POST | `/api/learners/` | Learners |
| POST | `/api/learners/bulk-import/` | CSV import |
| GET | `/api/learners/{id}/guardians/` | Linked guardians |
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
| GET, POST | `/api/courses/assignments/` | Assignments |
| POST | `/api/courses/progress/mark-complete/` | Idempotent progress update |
| GET, POST | `/api/courses/submissions/` | Submissions |
| POST | `/api/courses/submissions/{id}/grade/` | Grade a submission |
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
| GET, POST | `/api/curriculum/rubrics/` | Rubrics |
| GET, POST | `/api/curriculum/evidence/` | Competency evidence |
| GET, POST | `/api/content/textbooks/` | Textbook catalogue |
| POST | `/api/content/textbooks/{id}/publish/` | Publish a title |
| GET | `/api/content/available/` | Titles licensed to your institution |
| GET, POST | `/api/content/chapters/` | Chapters |
| GET, POST | `/api/content/resources/` | Audio, video, PDF, links |
| GET, POST | `/api/content/exercises/` | Chapter exercises |
| GET, POST | `/api/content/exercise-attempts/` | Exercise attempts |
| GET, POST | `/api/content/access/` | Licence grants |

## Communication and reports

| Method | Endpoint | Purpose |
|---|---|---|
| GET, POST | `/api/communications/announcements/` | Announcements |
| POST | `/api/communications/announcements/{id}/publish/` | Publish |
| GET | `/api/communications/notifications/` | Own notifications |
| POST | `/api/communications/notifications/mark-all-read/` | Mark read |
| GET, POST | `/api/communications/messages/` | Direct messages |
| GET | `/api/reports/dashboard/` | School dashboard figures (staff only) |
| GET | `/api/reports/analytics/` | Chart-ready attendance, exam and learner status data (staff only) |
| GET | `/api/reports/my-learners/` | Learners the caller may open (for report pickers and portal home) |
| GET | `/api/reports/learner/{id}/` | Learner report (scoped by institution, link and guardian permissions) |
| GET, POST | `/api/reports/snapshots/` | Saved reports |

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
`frontend/src/services/api.js`, which needs a live connection and does **not**
queue the upload offline. After a successful save, the UI refreshes
`/api/auth/me/` so both layouts show the new logo.

The migration behind these fields is
`backend/apps/institutions/migrations/0002_institution_logo_institution_motto_and_more.py`.
A backup was taken first at `backups/lms_20261123_134452.sql`.

## Response conventions

- List endpoints are paginated: `{"count", "next", "previous", "results"}`.
  Use `listAll()` in the frontend to flatten them.
- Validation errors return HTTP 400 with field-name keys.
- Cross-institution detail requests return 404, not 403.
- Timestamps are timezone-aware (`Africa/Nairobi`).
