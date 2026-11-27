# Product direction — Learners Management System

Status: **Approved foundation; Phase 1 in progress**. This document is the
source of truth for purpose and scope. Feature work should reference it before
code is written.

**Direction change (24 November 2026, supersedes earlier offline goals):** the
product is a **normal web app**, not a PWA or native app. The broad IndexedDB
mutation queue, sync/conflict pages and banners, service worker, PWA manifest,
workbox precache, Capacitor config and the `frontend/android` /
`frontend/ios` directories were removed. Failed mutations surface an error and
remain unsaved; uploads need a live connection. A manual deployment kill-switch
for previously installed service workers is documented in
`PRODUCTION_CONFIGURATION.md`.

**Documented narrow reversal (26 November 2026):** an env-driven low-bandwidth
mode now supports a small public read cache and allowlisted theming `PATCH` /
`DELETE` writes on an already-loaded page. It is off by default, stores no
credentials or person-like fields, uses `If-Match` with 409 conflicts, and adds
no service worker, PWA shell or native wrapper. See `OFFLINE_MODE_REVERSAL.md`.
See `README.md` and `SECURITY_AUDIT.md` for the current security posture and
verification limits.

## What we are building

A single, maintainable **Learners Management System (LMS)** for a Kenyan
educational publishing and school context. It brings together three connected
experiences:

1. **Public website** — institutional information, learning-resource discovery,
   announcements, documents, videos and registration entry points.
2. **Learner Management Portal** — authenticated dashboards for learners,
   teachers and guardians, built around real records and role-appropriate work.
3. **Administration Portal** — restricted control of people, academic structure,
   content, media, navigation, branding, notifications and system configuration.

These are one product sharing one backend and one database. They are separated
by route and permission, not by separate codebases.

## Problem being solved

Learners, teachers and guardians currently have to piece together information
from scattered pages, documents and messages. Administrators have no single
place to organise people, resources, academic structure and public content
without editing source code.

The system should replace that fragmentation with:

- one trusted record of each learner, class, subject and resource;
- one place to find and access learning materials;
- one role-appropriate view of what each person needs to do or know;
- one administration surface for everything that changes in the product.

## Vision

> Every learner is supported by one trusted, accessible place where people,
> learning resources and academic information meet.

## Mission

> To organise learner management and access to educational resources around the
> learner, so that teachers can teach, learners can learn and guardians can stay
> informed without technical friction.

## Objectives

| # | Objective | How success looks |
|---|---|---|
| O1 | Learner-centred data | Courses, classes, assignments, assessments, attendance, resources, reports and guardians connect to a learner record |
| O2 | Discoverable resources | A learner or teacher can find a resource by level, subject, class, collection or keyword in a few steps |
| O3 | Role clarity | Each of the four user categories sees only the dashboard, records and actions relevant to them |
| O4 | Admin configurability | Content, pages, media, navigation, announcements, branding and key settings are changed in the admin panel, not in source |
| O5 | Usable everywhere | Desktop, tablet and mobile layouts are responsive, readable and reachable on low bandwidth |
| O6 | Honest, reliable web behaviour (broad offline objective superseded) | Failed edits show an error and remain unsaved by default; the user can retry with a live connection. If explicitly enabled, only allowlisted non-personal reads and theming writes are cached/queued, with visible conflicts |
| O7 | Security and accountability | Permissions are enforced on the backend, writes are audited, and public registration cannot create admin accounts |
| O8 | Maintainability | Features live in modular apps with shared components and documented contracts; no feature requires duplicating another |

## Core functionality

### Public

- Institutional story, mandate, leadership and contact information.
- Searchable learning-resource catalogue with filters and previews.
- Documents and forms library.
- Announcements and news.
- Registration entry for learner, teacher and guardian.
- Accessibility options and clear help routes.

### Authenticated portal

- Role-specific dashboard: what is mine, what is due, what changed.
- Learner: subjects, classes, resources, assignments, assessments, progress and profile.
- Teacher: assigned classes and learners, resources, assignments, assessments, communication and profile.
- Guardian: linked learners, progress, reports, announcements and communication.
- Clear error states when a write or upload fails; the change stays unsaved
  until the user retries. Where low-bandwidth mode is explicitly enabled, only
  allowlisted theming writes show a queue/conflict status.

### Administration

- People and accounts: learners, teachers, guardians, administrators and custom roles.
- Academic structure: institutions, departments, years, terms, classes, subjects and timetables.
- Learning resources: documents, videos, links, textbooks and collections.
- Website content: pages, sections, announcements, navigation and media.
- Appearance: active palette, logos and visual settings.
- Configuration: permissions, notifications and relevant system settings.
- Monitoring: reports, activity logs, audit trail and basic performance views.

## Value by user

| User | What they need | Value delivered |
|---|---|---|
| Administrator | Complete, protected control of the platform | One place to manage people, content, structure and appearance without code changes |
| Teacher | Assigned classes, learners and teaching resources | Faster preparation, assessment and communication with a clear workload view |
| Learner | Resources, assignments and progress in one place | Less searching, more independent learning and visible progress |
| Guardian | Trustworthy information about a linked learner | Confidence and timely awareness without needing to understand the system |

## Three-experience rule

Every proposed feature must be placed explicitly:

- **Public** — usable before sign-in and safe to show to anyone.
- **Portal** — requires authentication and is scoped to the user's role and records.
- **Administration** — restricted to authorised administrators and changes shared state.

If a feature does not fit one of these, it needs a stronger reason to exist.

## Feature test

Before implementing anything, answer:

1. Which user category does this serve?
2. Which learner-management or resource-access problem does it solve?
3. Which of the three experiences owns it?
4. What record is the source of truth?
5. What permission governs read and write access?
6. Is it configurable in the admin panel where non-technical change is expected?
7. Does it remain usable on mobile, and does it fail honestly when the
   connection drops? Any local save or replay must stay within the narrow, env-driven, non-personal allowlist.
8. Can it be tested without inventing passwords or demo data?

A feature that cannot answer these questions is not ready for implementation.

## Decisions confirmed — 24 November 2026

> **Current-state note:** the delegated platform/school administrator decision
> below is historical and is superseded by the simplified role model: built-ins
> are `SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER` and `GUARDIAN`.
> Retired `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and
> `CONTENT_MANAGER` accounts migrate to `ADMIN` without password changes.
> `SUPER_ADMIN` is unchanged. Custom roles pick capabilities, enter `/admin`
> only with `admin.access`, and are enforced by the backend. See
> `USER_ROLES_JOURNEYS.md`.

- **Primary administrator:** one seeded `SUPER_ADMIN` has complete control.
  Delegated `PLATFORM_ADMIN`, `INSTITUTION_ADMIN` and `SCHOOL_ADMIN` accounts
  remain available, but only through expiring, single-use invitations created by
  an authorised administrator. They cannot self-escalate. School admins retain
  palette/theme management as previously chosen.
- **Registration approval:** learners and guardians may self-register. Teacher
  accounts are created inactive and become usable only after an administrator
  approves them and assigns their scope. Admin accounts are invitation-only.
- **Guardian linking:** a guardian proposes a learner identifier/code during
  registration; the link is verified before any learner data is visible. The
  existing `LearnerGuardian` API is the source of truth.
- **CMS depth:** public content becomes progressively database-driven. Start
  with pages/sections, navigation, media and announcements in Phase 5; do not
  build a full page builder before Phase 1.
- **Media and video:** local uploads are the default, and curated external video
  embeds are allowed only through an admin-managed allowlist with URL validation.
  No arbitrary iframe or script injection is permitted.
- **Registration fields:** Phase 1 uses the current serializer fields plus the
  minimum role-specific additions documented in `USER_ROLES_JOURNEYS.md`.
- **Implementation authorisation:** the foundation and Phase 1 were approved on
  24 November 2026. Work proceeds one module at a time with tests.
- **Web-only product direction:** broad offline/PWA/native work was explicitly
  removed later on 24 November 2026. The later narrow, env-driven low-bandwidth
  mode is a separately documented reversal, not a return to PWA/native.
  Authentication is session-cookie based and roles are re-read from
  `/api/auth/me/`. Security hardening is recorded in `SECURITY_AUDIT.md`;
  **production readiness is not claimed** until deployment/runtime verification
  is complete.

## Implementation checks — not blockers

- Administrator and custom-role permissions follow the matrix in
  `USER_ROLES_JOURNEYS.md` and are rechecked before each new admin screen is
  added; every picked capability is enforced by the backend.
- Production media hosting remains a deployment decision; local storage and
  validated external embeds are the application-level scope for now.

See `docs/FUNCTIONAL_REQUIREMENTS.md`, `docs/USER_ROLES_JOURNEYS.md`,
`docs/SYSTEM_ARCHITECTURE.md`, `docs/CURRENT_STATE_AUDIT.md`,
`docs/DEVELOPMENT_ROADMAP.md` and `docs/REFERENCE_REVIEW.md` for the detailed plan.
