# Originally requested vs implemented

This is a plain-language comparison. “Requested” comes from the 21-section
research brief and the phased plan in the parent folder. “Implemented” is what
exists in this repository today and has been exercised in this project.

**Completion answer: not 100%.** Phases 0–6 are mostly implemented and the
foundation is working. Several Phase 2/3 ideas from the research report were
never requested for this build; the old Phase 7 was a foundation, Phase 8 is
partial and Phase 9 is not complete.

**Supersession notice (24 November 2026):** this table is a historical
request/implementation comparison. Rows that mention a PWA, service worker,
offline queue, Capacitor or native apps describe an earlier milestone and are
**no longer implemented**. The product is now a normal web app only: the queue,
service worker, PWA manifest/workbox precache, Capacitor config and
`frontend/android` / `frontend/ios` were removed. Failed mutations surface an
error and remain unsaved; uploads require a live connection. Authentication is
session-cookie based with CSRF and `/api/auth/me/` identity reads. Deployment
and runtime verification are still outstanding; see `README.md` and
`SECURITY_AUDIT.md`.

| # | Originally requested | Implemented here | Status |
|---|---|---|---|
| 1 | Strategic research report in 21 sections, with evidence labels and five reference systems | `Kenyan_Digital_Learning_Ecosystem_Strategy_Report.md` and `.docx` in the parent folder | **Implemented** |
| 2 | One connected platform: LMS + SIS + Digital Publishing | 20 Django apps behind one REST API; one React web app *(historically a PWA; PWA removed)* | **Implemented (web app)** |
| 3 | Django/DRF + PostgreSQL `lms`, React/Vite, modular monolith | Pinned versions, `.env` configuration, modular apps *(historically also a PWA service worker; removed)* | **Implemented** |
| 4 | Roles and institution isolation | Custom user roles, shared queryset scoping, forced institution on writes, tests for cross-school smuggling | **Implemented** |
| 5 | School, learner, teacher and guardian records | CRUD pages and endpoints; guardian links with view permissions | **Implemented** |
| 6 | Classes, subjects, timetable and attendance | Classes/subjects pages, timetable endpoints, attendance register and charts | **Implemented** |
| 7 | Bulk learner import | CSV endpoint with transactional validation | **Implemented** |
| 8 | Courses, modules, lessons and progress | Course CRUD plus dedicated Modules/Lessons pages and progress endpoint | **Implemented (core)** |
| 9 | Assignments, submissions, quizzes, attempts and exams | CRUD and grading/auto-marking endpoints; list/create UI | **Implemented (core)** |
| 10 | Kenyan CBE: frameworks, levels, learning areas, strands, outcomes, competencies, rubrics, evidence | Version-aware models, endpoints and Curriculum page | **Implemented (structures)** |
| 11 | Digital textbooks, chapters, resources, exercises and licences | Catalogue, chapter/resource pages, licence model and access checks | **Implemented (foundation)** |
| 12 | Parent/guardian access and school reports | Guardian links, scoped `my-learners`, individual report with permission flags, messages | **Implemented (foundation)** |
| 13 | Offline PWA with queued writes | **Superseded/removed.** The service worker, cached reads, IndexedDB queue, Sync now and conflict UI were built in an earlier milestone and then deleted. Failed mutations now surface an error and remain unsaved; uploads require a live connection | **Removed by product direction change** |
| 14 | Automatic unique reference numbers | Central advisory-lock generator; admission/staff/course/subject/textbook codes | **Implemented** |
| 15 | Responsive charts, graphs and visual reports on desktop and mobile | Recharts cards on Dashboard and Reports; `ResponsiveContainer`, CSS grid and mobile breakpoints | **Implemented in this milestone** |
| 16 | Every dashboard card, menu item and section clickable | KPI cards link to records, Refresh button, quick links, admin actions, mobile menu toggle | **Implemented in this milestone** |
| 17 | Production settings and secret handling | `config.settings_prod`, `MAILERS`, `.env.example`, no passwords in source docs. Now fail-closed on `PRODUCTION_SECRET_KEY`, SMTP host, allowed hosts and CORS origins; local `.env` remains Git-ignored and owner-managed; `backups/` is Git-ignored (hashes/PII) | **Implemented; deployment verification pending** |
| 18 | Automated and browser testing | **Historical result:** backend 100 passed, frontend 62 across 22 files after the (now removed) Capacitor dependency change and the Ocean Blue palette change. **Current result:** frontend **101 tests across 32 files**, full backend **221 passed**, clean web-only build, `npm audit --audit-level=moderate` **0 vulnerabilities**, focused backend auth/account/core/tutor/KEMIS/security suite **71 passing**; live browser checks covered auth animations, session login and `/portal`; forced reduced-motion browser checks passed at desktop and 390 px. Deployment/runtime and assistive-technology checks remain outstanding | **In progress; not production-ready** |
| 19 | Fees and payments | School-office fee structures, invoices and recorded payments with balances, role-scoped ledger, portal invoice view, labelled samples and no gateway/card data | **Implemented (ledger only)** |
| 20 | SMS/USSD fallback and native apps | **Superseded/removed.** Capacitor config, dependencies, scripts and the `frontend/android` / `frontend/ios` directories were deleted. No signed APK/IPA, native plugins or SMS/USSD gateway | **Removed by product direction change** |
| 21 | KICD approval workflow for publishing | Internal request → checklist → submit → review/decision workflow with role-scoped endpoints and labelled samples; no submission to KICD and no claim of official approval | **Implemented (internal workflow only)** |
| 22 | Mastery gradebook and analytics-to-remediation rules | Snapshots, remediation rules and learner-scoped support tasks with complete/dismiss actions; not a full warehouse and no model training | **Implemented (local rules only)** |
| 23 | KEMIS reporting/export | Local export staging with dataset/mapping views, CSV/JSON download and explicit template warning; no transmission, credentials or official-template validation | **Implemented (local staging only)** |
| 24 | Advanced analytics warehouse, LTI marketplace and bounded AI tutor | Rule-based analytics plus deterministic, curriculum-grounded local tutor with source labels and optional env-only HTTP provider; no warehouse, LTI marketplace or bundled AI credentials | **Partial** |
| 25 | Full accessibility audit and independent security review | Lighthouse accessibility **1.00** on the public homepage after contrast fixes; responsive layout and semantic controls verified. The canvas headline keeps a real `<h1>` and reduced-motion support. Assistive-technology audit (including the canvas) and independent third-party security review still outstanding | **Partial** |
| 26 | Public production deployment, load test and monitoring | Settings prepared; no deployment performed | **Not implemented** |
| 27 | Separate staff and learner/guardian sides | Public `/` homepage; `/admin/...` with `DashboardLayout`; `/portal/...` with `PortalLayout`; `RoleHome` redirects old URLs by role | **Implemented and browser-verified by role** |
| 28 | School self-service profile and logo | `GET/PATCH /api/institutions/mine/`, `/admin/school`, logo in both layouts through `institution_logo` | **Implemented; API tests passed** |
| 29 | Invitation-only administrator signup | Expiring single-use server-side token, role/institution fixed by the invitation, public registration limited to learner/guardian/teacher | **Implemented** |
| 30 | RBAC enforced on backend and frontend | Central write mixins, role/capability checks, self-escalation block, `ManagedResourcePage` action flags, role guards; custom roles need `admin.access` for `/admin` and all other capabilities are backend-enforced | **Implemented** |
| 31 | 10+ labelled sample records per input category | Add-only idempotent seeder, `.invalid` emails, `sample_` users, `SMP-`/`DEP-` codes; the former `SAMPLE DATA` UI badge was removed | **Implemented and verified** |
| 32 | Distinct education-oriented UI with a familiar product layout | Zeraki used only as a layout/information-hierarchy reference: hero, three photographed workspace cards, progress/insights section, interactive role selector with rights/content preview, editable footer config, KLB copy; duplicate quick links, static taglines and the later facts strip removed | **Implemented** |
| 33 | Approved Ocean Blue Serenity palette | *(Historical approval.)* White-dominant backgrounds; nine-step blue ramp applied to tokens, charts, web app metadata (`index.html`) and original SVGs; blue-only semantics with wording/border cues in that pass. *(Historically PWA metadata; manifest removed.)* Lighthouse **1.00** scores preserved. **Current status (25 November 2026):** Plum Harvest is active/default and status colours are fixed red/green/amber/blue | **Implemented and verified** |
| 34 | Runtime theme manager | Persistent palette catalogue, single active selection, public active read, admin CRUD/activation, CSS-variable application, chart/meta derivation, contrast validation and `/admin/theme` manager; **eight** built-in palettes seeded (Ocean Blue Serenity, Sage Green and six supplied swatch sets, including Plum Harvest), additional palettes onboarded through the UI. As of 25 November 2026, Plum Harvest is active/default after the local `theming.0004_seed_and_activate_plum_harvest` migration. `SUPER_ADMIN` and `ADMIN` may manage; a custom role needs `appearance.manage` | **Implemented and verified** |

## Why the project is not 100%

Several items 19–26 were future-phase ideas in the research report, and others
require external services, procurement, independent review or a production
environment. Some now have deliberately bounded local implementations (for
example an internal review workflow, local export staging and a deterministic
tutor). They are not hidden or re-labelled as official integrations or finished
native/deployment work. Everything marked implemented has been tested in this
project; everything marked partial or not implemented is listed honestly here
and in `HANDOVER_REPORT.md`. Offline/native items are now explicitly removed
rather than partial, and production readiness is not claimed.
