# Automatic reference numbers

Business identifiers are generated centrally by
`backend/apps/core/codes.py`. The UI leaves admission and staff-number fields
blank by default, so people enter a value only when they have an official one.

## Format

People use a month-scoped identifier:

```text
PREFIX_SCHOOL_YYYY/MM_NNN
TR_KSCH_2026/11_001
```

- `PREFIX` is `TR` (teacher), `LR` (learner) or `GD` (guardian).
- `SCHOOL` is a short abbreviation from the institution name, for example
  `KSCH` for Kisumu Secondary School or `NACA` for Nairobi Academy.
- `YYYY/MM` is the generation year and month; `NNN` is a three-digit sequence
  that increases per school and prefix within that month.

Other school-owned codes keep the `PREFIX-SCHOOL-SEQUENCE` shape, for example
`ASM-KSCH-001`, `CRS-KSCH-001` and `SUB-KSCH-001`. Institutions themselves use
`INST_YYYY_NNN`, for example `INST_2026_001`. Platform-wide records use a
global sequence, for example `PUB-0001`, `CFW-0001`, `TB-000001`.

These are visible reference strings, not database keys: primary keys and
foreign keys stay numeric. Where the username is left blank it is generated
from a sanitized `first_last` and made unique with a numeric suffix. The
identifiers are shown in the Users, Learners, Teachers and Guardians tables.

## Generated identifiers

| Model | Field | Example |
|---|---|---|
| `InstitutionType` | `code` | `TYP-001` |
| `Institution` | `code` | `INST_2026_001` |
| `Learner` | `admission_number` | `LR_KSCH_2026/11_001` |
| `Learner` | `assessment_number` | `ASM-KSCH-001` |
| `Teacher` | `staff_number` | `TR_KSCH_2026/11_001` |
| `Guardian` | `guardian_number` | `GD_KSCH_2026/11_001` |
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
by model, field and owner. Person identifiers use the same pattern keyed by
prefix, institution and year/month, so two learners or teachers registered at
the same instant receive different numbers. The lock is released when the
creating transaction commits or rolls back.

## Overriding a value

Send the field in the API payload if you need to use an official number. The
serializer validates duplicates before saving:

- admission, staff and guardian numbers are unique within an institution;
- subject and course codes are unique within an institution;
- assessment numbers are checked globally;
- publisher and curriculum framework codes are globally unique.

If the field is blank, the model's `AutoReferenceModelMixin` fills it, so
management commands, the Django admin and direct ORM code behave the same as
the REST API.

## Tests

`backend/apps/core/tests/test_reference_codes.py` covers institution codes,
school abbreviation, per-school person sequences (teacher, learner and
guardian), API creation without an admission number, publisher/textbook/chapter
numbering, and code uniqueness across institutions.
