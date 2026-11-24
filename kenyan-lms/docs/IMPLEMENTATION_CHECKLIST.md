# Originally requested vs implemented

This is a plain-language comparison. “Requested” comes from the 21-section
research brief and the phased plan in the parent folder. “Implemented” is what
exists in this repository today and has been exercised in this project.

**Completion answer: not 100%.** Phases 0–6 are mostly implemented and the
foundation is working. Several Phase 2/3 ideas from the research report were
never requested for this build; Phase 7 is a foundation, Phase 8 is partial
and Phase 9 is not complete.

| # | Originally requested | Implemented here | Status |
|---|---|---|---|
| 1 | Strategic research report in 21 sections, with evidence labels and five reference systems | `Kenyan_Digital_Learning_Ecosystem_Strategy_Report.md` and `.docx` in the parent folder | **Implemented** |
| 2 | One connected platform: LMS + SIS + Digital Publishing | 14 Django apps behind one REST API; one React PWA | **Implemented** |
| 3 | Django/DRF + PostgreSQL `lms`, React/Vite, modular monolith | Pinned versions, `.env` configuration, modular apps, PWA service worker | **Implemented** |
| 4 | Roles and institution isolation | Custom user roles, shared queryset scoping, forced institution on writes, tests for cross-school smuggling | **Implemented** |
| 5 | School, learner, teacher and guardian records | CRUD pages and endpoints; guardian links with view permissions | **Implemented** |
| 6 | Classes, subjects, timetable and attendance | Classes/subjects pages, timetable endpoints, attendance register and charts | **Implemented** |
| 7 | Bulk learner import | CSV endpoint with transactional validation | **Implemented** |
| 8 | Courses, modules, lessons and progress | Course CRUD plus dedicated Modules/Lessons pages and progress endpoint | **Implemented (core)** |
| 9 | Assignments, submissions, quizzes, attempts and exams | CRUD and grading/auto-marking endpoints; list/create UI | **Implemented (core)** |
| 10 | Kenyan CBE: frameworks, levels, learning areas, strands, outcomes, competencies, rubrics, evidence | Version-aware models, endpoints and Curriculum page | **Implemented (structures)** |
| 11 | Digital textbooks, chapters, resources, exercises and licences | Catalogue, chapter/resource pages, licence model and access checks | **Implemented (foundation)** |
| 12 | Parent/guardian access and school reports | Guardian links, scoped `my-learners`, individual report with permission flags, messages | **Implemented (foundation)** |
| 13 | Offline PWA with queued writes | Service worker, cached reads, IndexedDB mutation queue and Sync now exist. Stale writes are rebased once against the current server version; unresolved conflicts remain visible for manual review. No fresh offline replay on a physical device | **Implemented (foundation); not complete** |
| 14 | Automatic unique reference numbers | Central advisory-lock generator; admission/staff/course/subject/textbook codes | **Implemented** |
| 15 | Responsive charts, graphs and visual reports on desktop and mobile | Recharts cards on Dashboard and Reports; `ResponsiveContainer`, CSS grid and mobile breakpoints | **Implemented in this milestone** |
| 16 | Every dashboard card, menu item and section clickable | KPI cards link to records, Refresh button, quick links, admin actions, mobile menu toggle | **Implemented in this milestone** |
| 17 | Production settings and secret handling | `config.settings_prod`, `MAILERS`, `.env.example`, no passwords in source docs | **Implemented** |
| 18 | Automated and browser testing | Backend 95 passed, frontend 52 passed across 19 files. Final build, audit, deploy and health checks repeated cleanly after the Capacitor dependency change. Browser sweep covered public, admin and portal routes plus the new fees, approval, KEMIS, tutor, analytics and sync modules at 1440×900 and emulated 390×844 with no console errors or horizontal overflow. Destructive submissions, logo upload and fresh offline replay remain untested | **Mostly implemented** |
| 19 | Fees and payments | School-office fee structures, invoices and recorded payments with balances, role-scoped ledger, portal invoice view, labelled samples and no gateway/card data | **Implemented (ledger only)** |
| 20 | SMS/USSD fallback and native apps | Capacitor config, pinned dependencies and documented build steps for the same PWA bundle; no signed APK/IPA, native plugins or SMS/USSD gateway | **Partial (wrapper scaffolding only)** |
| 21 | KICD approval workflow for publishing | Internal request → checklist → submit → review/decision workflow with role-scoped endpoints and labelled samples; no submission to KICD and no claim of official approval | **Implemented (internal workflow only)** |
| 22 | Mastery gradebook and analytics-to-remediation rules | Snapshots, remediation rules and learner-scoped support tasks with complete/dismiss actions; not a full warehouse and no model training | **Implemented (local rules only)** |
| 23 | KEMIS reporting/export | Local export staging with dataset/mapping views, CSV/JSON download and explicit template warning; no transmission, credentials or official-template validation | **Implemented (local staging only)** |
| 24 | Advanced analytics warehouse, LTI marketplace and bounded AI tutor | Rule-based analytics plus deterministic, curriculum-grounded local tutor with source labels and optional env-only HTTP provider; no warehouse, LTI marketplace or bundled AI credentials | **Partial** |
| 25 | Full accessibility audit and independent security review | Lighthouse accessibility **1.00** on the public homepage after contrast fixes; responsive layout and semantic controls verified. Assistive-technology audit and independent third-party security review still outstanding | **Partial** |
| 26 | Public production deployment, load test and monitoring | Settings prepared; no deployment performed | **Not implemented** |
| 27 | Separate staff and learner/guardian sides | Public `/` homepage; `/admin/...` with `DashboardLayout`; `/portal/...` with `PortalLayout`; `RoleHome` redirects old URLs by role | **Implemented and browser-verified by role** |
| 28 | School self-service profile and logo | `GET/PATCH /api/institutions/mine/`, `/admin/school`, logo in both layouts through `institution_logo` | **Implemented; API tests passed** |
| 29 | Invitation-only administrator signup | Expiring single-use server-side token, role/institution fixed by the invitation, public registration limited to learner/guardian/teacher | **Implemented** |
| 30 | RBAC enforced on backend and frontend | Central write mixins, role-hierarchy checks, self-escalation block, `ManagedResourcePage` action flags, role guards | **Implemented** |
| 31 | 10+ labelled sample records per input category | Add-only idempotent seeder, `SAMPLE DATA` badge, `.invalid` emails, `sample_` users, `SMP-`/`DEP-` codes | **Implemented and verified** |
| 32 | Distinct education-oriented UI with a familiar product layout | Zeraki used only as a layout/information-hierarchy reference: hero, three photographed workspace cards, facts strip, progress/insights section, interactive role selector with rights/content preview, editable footer config, KLB palette and copy; duplicate quick links and static taglines removed | **Implemented** |

## Why the project is not 100%

Several items 19–26 were future-phase ideas in the research report, and others
require external services, procurement, independent review or a production
environment. Some now have deliberately bounded local implementations (for
example an internal review workflow, local export staging and a deterministic
tutor). They are not hidden or re-labelled as official integrations or finished
native/deployment work. Everything marked implemented has been tested in this
project; everything marked partial or not implemented is listed honestly here
and in `HANDOVER_REPORT.md`.
