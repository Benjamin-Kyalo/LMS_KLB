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

## Design note

The class teacher is stored on `teachers_teacherclassassignment`
(`is_class_teacher=True`), not on `schoolclass`. This avoids a circular
foreign-key dependency between the `institutions` and `teachers` apps.

## Inspect the database safely

```powershell
$env:PGPASSWORD="your-password"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d lms -c "\dt"
```
