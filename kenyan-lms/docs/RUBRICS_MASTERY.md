# Rubrics and mastery

This guide describes the implemented assessment workflow. It uses the existing
`Rubric`, `RubricLevel`, `Competency` and `CompetencyEvidence` models; no second
rubric system was introduced. No marks or feedback are generated automatically:
the server validates and totals marks supplied by staff, and staff choose when
to release feedback.

## Who may do what

| Action | Access |
|---|---|
| Build school rubrics, bands, criteria and comment bank | `SUPER_ADMIN`, `ADMIN`, `TEACHER`, or `CUSTOM` with `assessments.manage` |
| Change a global rubric template | `SUPER_ADMIN` only |
| Attach a rubric to an assignment and set attempt limits | Staff with assignment write access |
| Grade and publish a submission | Staff with assessment write access |
| Read published feedback | The owning learner; verified guardians with `can_view_academics` |
| Resubmit | Owning learner only, while `current_attempt < max_attempts` |

Reads remain institution-scoped. Detail access returns 404 for records outside
the caller's scope rather than revealing their existence.

## Rubric structure

- **Rubric** — a named template, either global (`institution = null`) or owned
  by one institution.
- **Achievement band** (`RubricLevel`) — a named percentage range from `0` to
  `100`. Bands describe the final percentage of the assignment, not raw
  criterion points. The API rejects negative minima, maxima above 100 and
  inverted ranges.
- **Criterion** (`RubricCriterion`) — one scored row in the marking grid, with a
  positive `max_score` and a display `sequence`.
- **Feedback comment** (`FeedbackComment`) — an optional reusable phrase with a
  category. School and global phrases are visible to their respective staff;
  only `SUPER_ADMIN` may change global phrases.

The builder lives at `/admin/rubrics`. Changes are sent through
`/api/curriculum/rubrics/`, `/api/curriculum/rubric-levels/`,
`/api/curriculum/rubric-criteria/` and `/api/curriculum/feedback-comments/`.
Every create, update and delete writes an institution-scoped `rubric.*` or
`feedback_comment.*` audit entry. Deleting a definition does not alter stored
grades because each attempt keeps its own snapshot.

## Marking an assignment

1. On `/admin/assignments`, choose a rubric (optional), set the assignment
   maximum, and enable resubmission with a maximum attempt count.
2. On `/admin/submissions`, open **Grade**. For a rubric assignment, enter a
   score and optional comment for each criterion; for a direct-score assignment,
   enter a score out of the assignment maximum.
3. `POST /api/courses/submissions/{id}/grade-rubric/` is strict. It rejects a
   criterion outside the assignment's rubric, duplicate criteria, a score above
   the criterion limit and a total above the assignment maximum. The server
   writes `SubmissionCriterionScore` rows for the current attempt, totals the
   marks, resolves the matching `RubricLevel` percentage band, and records an
   `SubmissionAttempt` history row.
4. Saving a grade does **not** notify the learner. **Publish feedback** calls
   `/api/courses/submissions/{id}/publish-feedback/`, which sets the publication
   timestamp, sends a `Notification` to the learner and to verified guardians
   whose academic permission is enabled, and writes an audit entry.
5. `private_notes` are for staff only. They are removed from every non-staff
   serializer response and are never included in a notification.

If a submission is published and the assignment allows another attempt, the
learner uses `/portal/submissions` to send new text and/or a file. The action
calls `/api/courses/submissions/{id}/resubmit/`, is limited to the owning
learner, and checks the attempt limit server-side. Earlier answers and grades
remain in the attempt history.

## Mastery evidence and derived badges

Existing competency records remain the source of truth for mastery:
`Competency` defines a skill, `RubricLevel` can describe its achieved band, and
`CompetencyEvidence` records the learner, outcome, competency, evidence type,
level and notes. Published rubric grades can inform a teacher's judgement, but
the system does not silently convert a criterion score into competency mastery.
A teacher records evidence explicitly through `/api/curriculum/evidence/`; that
view is staff-scoped and stamps the institution and recorder server-side.

Badge displays are derived read-only from that evidence. `build_mastery_badges()`
in `apps/analytics/engine.py` averages the existing 0–1 mastery scores per
learner and competency, then maps the average to the highest reached band:
`BEGINNING` 0.25, `DEVELOPING` 0.50, `ACHIEVING` 0.75 and `EXTENDING` 1.00. Only
`ACHIEVING` and `EXTENDING` count as earned; the lower two bands show progress.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/analytics/mastery/` | School-wide badge displays, rules and counts for staff |
| GET | `/api/analytics/my-mastery/` | The signed-in learner's own badge displays only |

Optional staff filters are `learner`, `competency` and `mastery_level`. An
unknown level returns a short field-level validation error. The response includes
`rules`, `summary` and `badges`, with each badge carrying its source evidence
count and latest evidence date. Notes and raw evidence text are not returned.

No badge table, award record, notification or audit row is created by these
endpoints. They are displays of existing data, not credentials, and automatic
awarding remains out of scope until separately requested and documented. The
staff screen is `/admin/mastery`; learners use `/portal/mastery`.
