# Sample data guide

The local project ships with add-only, clearly labelled fictional records so
every input category can be demonstrated without inventing real school data.

## Command

```powershell
cd "C:\Users\Admin IT\Downloads\LMS\LMS\kenyan-lms\backend"
.\.venv\Scripts\python.exe manage.py seed_sample_data
```

The command is idempotent: run it as often as needed. The final verification
run created **0** new records because all labelled records already existed.

## Labelling rules

- Users have `sample_` usernames and `.invalid` email addresses.
- Most business codes start with `SMP-`; departments use `DEP-...`.
- Text fields that are obviously fictional start with `SAMPLE`.
- The admin and portal layouts show a **SAMPLE DATA** badge when the signed-in
  institution uses a demo code such as `DEMO01`. The public homepage has no
  sample-data banner; the labelling remains visible in the authenticated apps
  and in the records themselves.
- No sample account stores a usable password created by the seeder. Admin-created
  records use unusable passwords and must use the password-reset flow.
- The seeder never prints a password.

## Verified category counts

The command reports each category and requires at least 10 records. The final
run reported `[OK]` for all of these categories:

| Area | Counts |
|---|---|
| Accounts and institutions | `accounts.User` 46; `InstitutionType` 12; `Institution` 10; `AcademicYear` 10; `Term` 30; `SchoolClass` 12; `Subject` 12; `Department` 12 |
| People | `Learner` 18; `LearnerGuardian` 15; `TransferRecord` 10; `Teacher` 13; `TeacherClassAssignment` 13; `LessonPlan` 12; `Guardian` 13 |
| School day | `TimetableEntry` 12; `SchoolEvent` 49; `AttendanceRecord` 245 |
| CBE curriculum | `CurriculumFramework` 10; `EducationLevel` 13; `LearningArea` 13; `Strand` 13; `SubStrand` 13; `LearningOutcome` 13; `Competency` 12; `Rubric` 10; `RubricLevel` 40; `CompetencyEvidence` 12 |
| Courses | `Course` 13; `Module` 25; `Lesson` 25; `LessonProgress` 144; `Assignment` 13; `Submission` 72 |
| Assessment | `Question` 26; `Quiz` 13; `QuizQuestion` 26; `QuizAttempt` 72; `Answer` 144; `Exam` 13; `ExamResult` 145 |
| Publishing | `Publisher` 13; `DigitalTextbook` 13; `Chapter` 25; `ContentResource` 24; `Exercise` 25; `ExerciseAttempt` 72; `ContentAccess` 13 |
| Communication and reporting | `Announcement` 13; `Notification` 12; `Message` 12; `NotificationPreference` 12; `ReportSnapshot` 15; `AuditLog` 12 |

`SchoolEvent` is above 10 because early reruns created duplicates before the
dedupe rule was corrected. No sample data was deleted to make the number tidy.

## Caveats

- Generated textbook ISBNs are local catalogue identifiers, not publisher-issued
  ISBNs. Replace them when real ISBNs are supplied.
- These records are for demonstration and local testing only. Remove or reseed
  before a real deployment.
- The seeder adds records; it does not repair or overwrite user edits.
