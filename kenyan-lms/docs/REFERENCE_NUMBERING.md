# Automatic reference numbers

Business identifiers are generated centrally by
`backend/apps/core/codes.py`. The UI never asks a user to invent an
admission number or staff number unless they have an official one to enter.

## Format

School-owned records use:

```text
PREFIX-SCHOOLCODE-SEQUENCE
ADM-KSCH-003
```

- `PREFIX` identifies the record type (`ADM`, `TCH`, `CRS`, `SUB`, `ASM`).
- `SCHOOLCODE` comes from `Institution.code`. If it is blank when the school
  is created, it is generated from the school name: `Kisumu Secondary School`
  becomes `KSCH`, `Nairobi Academy` becomes `NACA`. A duplicate name gets a
  numeric suffix (`KSCH2`).
- `SEQUENCE` is zero-padded to three digits and increases independently for
  each school and each field.

Platform-wide records use a global sequence, for example `PUB-0001`,
`CFW-0001`, `TB-000001`.

## Generated identifiers

| Model | Field | Example |
|---|---|---|
| `InstitutionType` | `code` | `TYP-001` |
| `Institution` | `code` | `KSCH` |
| `Learner` | `admission_number` | `ADM-KSCH-001` |
| `Learner` | `assessment_number` | `ASM-KSCH-001` |
| `Teacher` | `staff_number` | `TCH-KSCH-001` |
| `Subject` | `code` | `SUB-KSCH-001` |
| `Course` | `code` | `CRS-KSCH-001` |
| `Publisher` | `code` | `PUB-0001` |
| `DigitalTextbook` | `isbn` | `TB-000001` |
| `ContentAccess` | `licence_reference` | `LIC-KSCH-000001` |
| `CurriculumFramework` | `code` | `CFW-0001` |
| `EducationLevel` | `code` | `LVL-CFW-0001-001` |
| `LearningArea` | `code` | `LA-LVL-CFW-0001-001-001` |
| `Strand` | `code` | `STR-...` |
| `SubStrand` | `code` | `SS-...` |
| `LearningOutcome` | `code` | `LO-...` |
| `Competency` | `code` | `CMP-...` |
| `Chapter` | `chapter_number` | 1, 2, 3 within one textbook |

Curriculum codes imported from KICD are preserved. Generation only fills a
blank field, so official codes are never overwritten. A `Chapter` whose
supplied `chapter_number` already exists in that textbook is moved to the
next free number.

## Concurrency

`next_reference()` takes a PostgreSQL transaction-scoped advisory lock keyed
by model, field and owner. Two learners registered at the same instant
therefore receive different numbers. The lock is released when the creating
transaction commits or rolls back.

## Overriding a value

Send the field in the API payload if you need to use an official number. The
serializer validates duplicates before saving:

- admission numbers are unique within an institution;
- staff and subject codes are unique within an institution;
- assessment numbers are checked globally;
- publisher and curriculum framework codes are globally unique.

If the field is blank, the model's `AutoReferenceModelMixin` fills it, so
management commands, the Django admin and direct ORM code behave the same as
the REST API.

## Tests

`backend/apps/core/tests/test_reference_codes.py` covers school abbreviation,
per-school sequences, API creation without an admission number, publisher/
textbook/chapter numbering, and code uniqueness across institutions.
