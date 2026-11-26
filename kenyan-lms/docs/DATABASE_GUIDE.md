# Database guide

Connection settings come from `.env`:

```env
DB_NAME=lms
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=5432
```

## How structure changes are made

Always through Django migrations:

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
```

Never delete or recreate the `lms` database to fix a migration. Take a backup
first (see `BACKUP_AND_RESTORE.md`).

## Table groups

| App | Key tables | Purpose |
|---|---|---|
| `accounts` | `accounts_user` | One login per person, with role and institution |
| `institutions` | `institutions_institution`, `academicyear`, `term`, `schoolclass`, `subject` | School structure; terms are configurable |
| `learners` | `learners_learner`, `learnerguardian`, `transferrecord` | Learner records and links to guardians |
| `teachers` | `teachers_teacher`, `teacherclassassignment`, `lessonplan` | Staff and allocations |
| `guardians` | `guardians_guardian` | Parent profiles |
| `academics` | `timetableentry`, `schoolevent` | Timetable and calendar |
| `attendance` | `attendance_attendancerecord` | One record per learner per day |
| `curriculum` | `curriculumframework`, `educationlevel`, `learningarea`, `strand`, `substrand`, `learningoutcome`, `competency`, `rubric`, `rubriclevel`, `competencyevidence` | Version-aware CBE structures |
| `courses` | `course`, `module`, `lesson`, `lessonprogress`, `assignment`, `submission` | LMS content and progress |
| `assessments` | `question`, `quiz`, `quizquestion`, `quizattempt`, `answer`, `exam`, `examresult` | Question bank, quizzes, exams |
| `content` | `publisher`, `digitaltextbook`, `chapter`, `contentresource`, `exercise`, `exerciseattempt`, `contentaccess` | Digital publishing and licensing |
| `communications` | `announcement`, `notification`, `message`, `notificationpreference` | Messaging |
| `reports` | `reportsnapshot` | Saved report snapshots |
| `core` | `auditlog` | Audit trail for important actions |

## Important relationships

- `accounts_user.institution` → `institutions_institution`
- `learners_learner.user` → `accounts_user` (one-to-one)
- `learners_learner.institution` → `institutions_institution`
- `learners_learner.class_room` → `institutions_schoolclass`
- `institutions_schoolclass.academic_year` → `institutions_academicyear`
- `courses_course.subject` → `institutions_subject`
- `courses_module.course` → `courses_course`
- `courses_lesson.module` → `courses_module`
- `curriculum_learningoutcome.sub_strand` → `curriculum_substrand`
- `content_chapter.textbook` → `content_digitaltextbook`
- `content_exercise.chapter` → `content_chapter`
- `assessments_quizquestion.quiz` → `assessments_quiz`

## Constraints and indexes worth knowing

- `unique_admission_per_institution` — admission numbers unique per school.
- `one_attendance_per_learner_per_day` — no duplicate daily attendance.
- `unique_submission_per_assignment` — one submission per learner per assignment.
- `unique_answer_per_attempt` — one answer per question per quiz attempt.
- `unique_textbook_access` — one licence grant per institution per title.
- Indexes on `(institution, status, ...)`, learner identifiers, dates and
  report-relevant fields.

## Failed writes are atomic

A failed save leaves no partial database rows and no orphaned files. The paths
wrapped in transactions include admin user creation; learner, guardian and
teacher create/edit; password change and reset; account activation; learner CSV
import; quiz attempts (every answer is validated before anything is written);
payments; tutor questions (the provider answer is produced before any write);
approvals; announcements; custom roles; analytics snapshots and remediation;
site-content and theme-palette edits; and the `seed_demo` command.

Public `GET /api/site-content/` is read-only and no longer inserts an empty
`SiteContent` row. Replaced or reset managed photos are deleted from storage
only after the database change commits, so a failed write cannot leave a broken
image reference.

Rollback regression tests live in
`backend/apps/core/tests/test_write_atomicity.py` (failed user creation, CSV
import rollback, invalid quiz submission and invalid site-content patch).

## Managed photos and section styles

Administrator-uploaded public-site photos must be JPG, PNG or WebP, at least
640×360 pixels and at most 5 MB. The server checks the file name, magic bytes
and decoded image, so renaming a file does not pass validation. Per-section
styles are checked against an allowlist; raw CSS is rejected. See
`PUBLIC_SITE_CONTENT.md` for the editor workflow.

## Design note

The class teacher is stored on `teachers_teacherclassassignment`
(`is_class_teacher=True`), not on `schoolclass`. This avoids a circular
foreign-key dependency between the `institutions` and `teachers` apps.

Primary and foreign keys stay numeric. Human-facing identifiers — admission,
assessment, staff and guardian numbers and record codes — are separate indexed
fields generated by `apps/core/codes.py` (see `REFERENCE_NUMBERING.md`). Never
put a visible code in a key column or a key in a visible identifier.

## Inspect the database safely

```powershell
$env:PGPASSWORD="your-password"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d lms -c "\dt"
```

## Pending database work

Not done yet: partitioning or archiving old academic years, reporting views,
migration-lock planning, and switching the application over to the
least-privilege `lms_app` role. The current backup, role status and completed
cleanup are recorded in `BACKUP_AND_RESTORE.md`.
