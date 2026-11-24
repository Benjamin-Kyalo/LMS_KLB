# Kenyan Digital Learning Ecosystem — Strategic Research and Technical Concept Report

**Prepared for:** Kenya Literature Bureau (KLB) strategic concept exploration  
**Research cut-off:** 23 November 2026  
**Document status:** Research-led concept and technical strategy. **Implementation note:** after this report was written, a working React/Django build was created in `kenyan-lms/`; this report remains the original concept and reference record. Current build status is in `kenyan-lms/docs/HANDOVER_REPORT.md`.  
**Evidence labels:** **[Verified]** = primary/official source or directly checked document; **[Claim]** = vendor or institutional self-description; **[Secondary]** = credible third-party source; **[Assumption]** = working inference to validate; **[Recommendation]** = proposed decision or direction.  
**Confidence rule:** Where sources conflict, both values are shown. Where a capability or statistic could not be verified, it is explicitly marked unverified rather than inferred.

---

## 1. Executive summary

### 1.1 The strategic opportunity

**[Verified]** Kenya is mid-transition from the 8-4-4 system to the 2-6-3-3-3 Competency-Based Curriculum/Competency-Based Education (CBC/CBE) structure. The Basic Education Curriculum Framework (BECF) was published in 2017. Seven core competencies anchor the curriculum. Grade 10 rolled out in January 2026, the final 8-4-4 KCSE sitting is expected in 2027, the first Kenya Certificate of Basic Education (KCBE) is expected in 2028, and the first CBE tertiary entry is expected in 2029. [BECF/KICD](https://kicd.ac.ke/)

**[Verified]** Assessment has changed from a single summative endpoint to a layered evidence system: KEYA in Grade 3, KPSEA in Grade 6, KJSEA in Grade 9, and KCBE in Grade 12. Under the current CBE design, the Grade 9 pathway score combines 60% KJSEA, 20% school-based assessment from Grades 7–8, and 20% KPSEA. For Grades 10 and 11, school-based assessment contributes 15% each, with a 70% final summative component in Grade 12. [KNEC](https://www.knec.ac.ke/)

**[Verified]** KLB is 100% government-owned, was established in 1947 as the East African Literature Bureau, and was renamed KLB in 1980. The KLB Act Cap. 221 covers publishing and distribution of digital and electronic materials. [Kenya Law](https://kenyalaw.org/)

**[Verified]** KLB's audited FY2022/23 financials show turnover of KSh 2.743bn, gross profit of KSh 1.027bn, and pre-tax profit of KSh 168.69m. [Treasury KLB FY2022/23 statements](https://treasury.go.ke/sites/default/files/financial%20statements/Kenya-Literature-Bureau-2022_2023.pdf)

**[Secondary]** A later secondary-source signal reports FY2025 turnover of KSh 1.828bn, net profit of KSh 12.2m, and a delayed KICD textbook payment of KSh 1.026bn. This is **not audited** and should be validated before use in board or investor materials.

**[Verified]** KLB has prior digital activity: the 2021 Opiq consortium included StarCloud, Risk Africa Innovatis, UNICEF and Liquid Intelligent Technologies. KLB's 2024 price list channels include klbbooks.com, Opiq, Amazon, eKitabu, Worldreader, Snapplify and KEC. [KLB](https://klb.co.ke/)

**Strategic conclusion [Recommendation]:** KLB's defensible position is not "another LMS." It is the **KICD-aligned learning content and assessment system of record for Kenyan schools** — a connected LMS, SIS and digital publishing platform built around the curriculum, assessment evidence, offline access, and KLB's publishing authority.

### 1.2 Why a generic LMS will not be enough

**[Verified]** The Kenyan environment has constraints that generic LMS products do not treat as first-class:

- **Connectivity and affordability:** CA data for Q3 FY2025/26 reports 84,090,298 SIM subscriptions; Q4 reports 87,999,998. Smartphones are 63.7% of connected devices, individual phone ownership is 53.7%, and internet use is 35.0%. Urban internet use is 56.6% versus 25.0% rural. Household computer ownership is 8.8%. Electricity access is around 79%. M-Pesa accounts for 89.1% of mobile money. Nairobi internet use is 64.7% versus West Pokot at 9.1%. [ Communications Authority of Kenya](https://ca.go.ke/)
- **Low ICT integration in schools:** MoE's 2026 quality report states that ICT integration remained low in most schools despite the presence of some devices. [Ministry of Education](https://www.education.go.ke/)
- **Legal and safeguarding duties:** the Data Protection Act Cap. 411C and its regulations require parental/guardian consent for child data (Section 33). Educational institutions must register under the Registration Regulations, LN 265/2021. [Kenya Law](https://kenyalaw.org/)
- **Curriculum approval:** KICD Act Cap. 211A Section 27 makes use of unapproved curriculum materials in covered institutions an offence. KICD standards exist for digital course materials, educational mobile apps, and LMS/e-distribution platforms. [Kenya Law](https://kenyalaw.org/) · [KICD](https://kicd.ac.ke/)
- **Accessibility:** Kenya Standard KS 2952-1:2022 and KS 2952-2:2022 apply, and KICD app standards require alt text, voiceover, larger/bold text, and adaptation for learners with disabilities. [KEBS](https://www.kebs.org/)

**[Recommendation]** The product must be offline-first, mobile-first, child-safe, KICD-aligned, and procurement-ready from day one.

### 1.3 Reference platform verdicts

| Platform | Verdict | Role in the concept |
|---|---|---|
| Zeraki | Strong Kenyan school operations and analytics integration, but marks-centric and not a full CBE competency system. | **Adapt:** analytics-to-remedial loop, admission-number sync, parent reports with fees, teacher phone mark entry. |
| ShuleSoft | Strong SIS/ERP breadth with integrated learning and parent communication. No documented offline mode. | **Adapt:** canonical student identity, event-driven modules, unified communication fabric, one parent action. |
| Moodle | Open source, extensible, strong offline app and competency model; operational burden is real. | **Borrow philosophy:** plugin architecture, roles-in-context, completion rules, competencies, reusable question banks. |
| Canvas | Best-in-class teaching workflow, outcomes, rubrics and parent app; licence-dependent, not a full SIS. | **Borrow interaction design:** modules, SpeedGrader-style feedback, mastery gradebook, criterion-based messaging, blueprints. |
| Eneza | Kenyan proof that SMS/USSD can reach learners where smartphones and data are unreliable; learning-impact evidence is mixed. | **Adapt selectively:** text-first access, minimal setup, low cost, fast feedback; do not copy unverified impact claims. |

### 1.4 The proposed product

**[Recommendation]** Build **KLB One Learning** as one ecosystem with three connected products:

1. **LMS** — courses, lessons, assessments, competencies, evidence, feedback, offline learning.
2. **SIS** — admissions, enrolment, attendance, timetables, gradebook, fees, reports, staff, parent links.
3. **Digital Content & Publishing Platform** — KICD-aligned authoring, approval workflow, versioning, licensing, distribution, analytics and rights management.

**[Recommendation]** The distinctive wedge is a **curriculum-to-evidence chain**:

> KICD curriculum code → KLB learning object → lesson/course → assessment item → rubric criterion → learner evidence → mastery status → teacher action → parent explanation → school/board report

This chain is the thing none of the five reference platforms fully owns in the Kenyan context.

### 1.5 Technical direction

**[Verified]** Moodle core is PHP/GPL-3.0; Canvas core is Ruby on Rails/AGPLv3; Django REST Framework supports Django 5.2/6.0/6.1 and Python 3.10–3.15; PostgreSQL 19 was released 19 November 2026 and supports ACID transactions, JSONB, full-text search, row-level security, replication and point-in-time recovery. [Moodle GitHub](https://github.com/moodle/moodle) · [Canvas GitHub](https://github.com/instructure/canvas-lms) · [DRF](https://www.django-rest-framework.org/) · [PostgreSQL](https://www.postgresql.org/)

**[Verified]** MDN documents service workers, Cache API, Background Sync/Fetch and IndexedDB as the core PWA offline building blocks, with explicit browser and storage-eviction limits. [MDN PWA offline guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation)

**[Recommendation]** Use a Django + DRF + PostgreSQL backend, a React/Next web frontend, a PWA offline layer by default, and native Flutter or React Native apps only where a device programme or app-store requirement justifies the cost.

### 1.6 Commercial direction

**[Verified]** Kenyan capitation figures reported include KSh 1,420 per primary learner, KSh 15,042 per junior school learner, and KSh 22,244 per secondary learner; later primary capitation of KSh 2,238 was reported. Term 1 2026 capitation release of KSh 44.245bn and total capitation of KSh 86.1bn were reported in 2026. [Ministry of Education](https://www.education.go.ke/)

**[Verified]** Public schools are moving to e-GP; 900 institutions had migrated by February 2026. Procurement-ready documentation and termly payment design are therefore required. [Treasury/e-GP](https://www.treasury.go.ke/)

**[Recommendation]** Commercial model: per-school annual subscription with per-learner bands, content/licence revenue separated from platform fees, a subsidised public-school tier, and an offline/SMS micro-tier for basic-phone access. Do not assume families can pay a large monthly fee.

---

## 2. Research method, evidence rules, and limitations

### 2.1 Method

This report is based on seven parallel research streams:

1. KLB and compliance research.
2. Kenyan education system research.
3. Zeraki and Eneza platform research.
4. Business and commercial model research.
5. ShuleSoft platform research.
6. Moodle and Canvas platform research.
7. UI/UX design direction research.

Direct follow-up research was also conducted on Django, DRF, PostgreSQL, PWA offline APIs, Flutter, Africa's Talking pricing, and AWS African regions.

### 2.2 Evidence rules

- **[Verified]** means the fact was traced to an official site, law, government document, developer documentation, or a directly checked primary source.
- **[Claim]** means the statement comes from the vendor but was not independently audited. Vendor reach, uptime and user numbers are always labelled this way.
- **[Secondary]** means a credible third party, such as GSMA, HundrED, Engineering for Change, NN/g, W3C or a university guide.
- **[Assumption]** means a working hypothesis. It must be validated before a business case is locked.
- **[Recommendation]** means a proposed design, architecture or commercial decision.

### 2.3 Limitations

- Live Moodle Docs were intermittently blocked; archived official Moodle Docs snapshots were used where needed.
- Canvas ScreenSteps guides were login-blocked; Instructure product pages, developer docs, press releases and community KB material were used.
- Direct Eneza site pages failed during the UI/UX stream; third-party verified sources were used.
- Screenshot URLs were collected but could not be visually inspected pixel-by-pixel in this environment. Visual lessons are based on the surrounding official product text.
- No independent security audit, accessibility audit, penetration test, or total-cost-of-ownership model was produced.
- Kenyan market figures change quickly; the research cut-off is 23 November 2026.

---

## 3. Kenya education landscape

### 3.1 System structure and transition

**[Verified]** Kenya's 2-6-3-3-3 structure replaces 8-4-4 with:

| Stage | Grades | Age range (typical) | Key transition |
|---|---|---|---|
| Pre-primary | 2 years | 4–5 | Early learning |
| Primary | Grades 1–6 | 6–11 | KEYA Grade 3, KPSEA Grade 6 |
| Junior school | Grades 7–9 | 12–14 | KJSEA Grade 9, pathway placement |
| Senior school | Grades 10–12 | 15–17 | SBA + KCBE Grade 12 |
| Tertiary/TVET | Post-12 | 18+ | CBE-entry cohorts from 2029 |

**[Verified]** The seven core competencies are communication and collaboration; self-efficacy; creativity and imagination; critical thinking and problem solving; citizenship; digital literacy; and learning to learn. [BECF/KICD](https://kicd.ac.ke/)

**[Verified]** Grade 10 launched in January 2026; the final 8-4-4 KCSE is expected in 2027; the first KCBE is expected in 2028; first CBE tertiary entry is expected in 2029.

**Implication [Recommendation]:** the platform must support overlapping cohorts: legacy KCSE users, transition Grade 10–12 users, and full CBE users. Do not hard-code one assessment model.

### 3.2 Governance and institutions

| Institution | Role | Product implication |
|---|---|---|
| Ministry of Education (MoE) | Policy, financing, school system, digital strategy | Reporting formats, capitation alignment, procurement readiness |
| KICD | Curriculum, curriculum materials approval, standards | Approval workflow, version control, material codes |
| KNEC | Assessment and examination numbers | Assessment number lifecycle, exam integrity, result formats |
| Basic Education | Primary/junior/senior school administration | School and learner records |
| TVET and university regulators | Post-secondary pathways | Pathway and articulation data |
| ODPC | Data protection enforcement | Child consent, DPIAs, data subject rights |
| KEMIS | Education management information | Interoperability and reporting |

**[Verified]** KNEC assessment numbers are issued in Grade 3 and used through Grade 12. [KNEC](https://www.knec.ac.ke/)

**[Verified]** KEMIS is replacing NEMIS as the national education management information system. [Ministry of Education](https://www.education.go.ke/)

### 3.3 Curriculum materials and publishing

**[Verified]** KICD approves textbooks and materials through the Orange Book process. The 2026 course-material submission procedure is verified. [KICD](https://kicd.ac.ke/)

**[Verified]** Curriculum design, not the textbook, is the authoritative specification. Textbooks and digital resources are derived materials that require alignment and approval.

**[Recommendation]** Treat the curriculum document as a versioned source of truth. Every digital learning object should carry:

- subject, level, strand, sub-strand;
- learning outcome and competency codes;
- assessment standard;
- KICD approval status and reference;
- language, accessibility metadata, licence and version;
- prerequisite and remediation links.

### 3.4 School calendar and operational rhythm

**[Verified]** The 2026 Kenyan calendar is: Term 1, 5 January–2 April; Term 2, 27 April–31 July; Term 3, 24 August–23 October; national assessments from 26 October. [Ministry of Education](https://www.education.go.ke/)

**Implication [Recommendation]:** billing, reporting, data sync, exam locks and school dashboards should be term-aware. Term boundaries should be configurable because private and international schools may differ.

### 3.5 Connectivity, devices and affordability

**[Verified]** Key figures from CA data: 84.09m SIM subscriptions in Q3 FY2025/26 and 88.00m in Q4; 63.7% smartphones among connected devices; 53.7% individual phone ownership; 35.0% internet use; 56.6% urban versus 25.0% rural internet use; 8.8% household computer ownership; around 79% electricity access; and M-Pesa at 89.1% of mobile money. [CA](https://ca.go.ke/)

**[Verified]** Nairobi internet use is 64.7% versus West Pokot 9.1%. This is a product-design fact, not a footnote.

**[Recommendation]** Design assumptions:

- The learner's primary device is a low-cost Android phone, often shared.
- The teacher's device may be a phone plus a shared staff computer.
- Connectivity is intermittent, expensive, or both.
- Zero-rated or offline content materially changes access.
- SMS/USSD remains a necessary fallback for some learners and parents.

### 3.6 Digital policy and infrastructure

**[Verified]** Relevant policy and infrastructure include the ICT Policy 2021, NESSP 2023–2027, KEMIS, the Kenya Education Cloud, DLP/Digischool, and KDEAP support covering 10,382 schools. [Ministry of Education](https://www.education.go.ke/)

**[Verified]** MoE's 2026 quality report found ICT integration remained low in most schools despite some devices being available.

**[Recommendation]** Do not sell "devices + software" as the core value. Sell workflow, curriculum alignment, evidence and support; let device programmes be a channel, not the product thesis.

---

## 4. Platform 1: Zeraki — deep analysis

### 4.1 Origin, users and purpose

**[Verified]** Zeraki is associated with Litemore Ltd, Kenya. Founding is reported as 2014 or 2015 depending on source. CEO is Isaac Nyangolo. [Zeraki](https://zeraki.app)

**[Verified]** Zeraki raised US$1.8m seed funding in December 2022, led by Acumen. [Acumen](https://acumen.org/)

**[Claim]** Acumen's 2025 profile reports more than 7,600 schools, 180,000 teachers, 3 million learners, and more than 60% of Kenyan secondary schools. These are vendor/investor-reported figures, not independently audited here.

**[Verified]** Zeraki's purpose is improving secondary-school teaching, assessment, analytics and parent visibility in Kenyan schools.

### 4.2 Products and features

**[Verified]** Zeraki products include:

- Zeraki Analytics — marks, performance analysis, reports, parent visibility.
- Zeraki Learning — video lessons, topical quizzes, simulations, exam papers with marking schemes, teacher notes, assignments, revision and progress tracking.
- Zeraki Finance — fee and school finance workflows.
- Zeraki Timetables.
- Zeraki Achievers.
- Zeraki Touch — biometric-style attendance/identification.
- Marketplace.

**[Verified]** "Zeraki Exams" was not verified as a standalone product. Do not present it as one.

**[Verified]** Zeraki Learning states content is KICD-approved. This is a vendor claim that should be checked against current KICD approval records before relying on it in KLB strategy. [Zeraki Learning](https://zeraki.app/zeraki-learning)

### 4.3 Learner, teacher, parent and admin experience

| Role | Verified evidence | Design implication |
|---|---|---|
| Learner | Video lessons, quizzes, simulations, exam papers, assignments and progress tracking. [Zeraki Learning](https://zeraki.app/zeraki-learning) | Strong revision experience; needs stronger competency evidence layer. |
| Teacher | Upload/check assignments, marks entry, performance analysis, bulk messaging. [Zeraki parent article](https://zeraki.app/post/parents-now-able-monitor-learner-s-perfomance-in-new-app) | Reduce duplicated entry; add rubric and SBA evidence. |
| Parent | Results analysis, reports, fee balance, bulk SMS. | Parent value is clear; explanation of competencies is weaker. |
| Admin | Analytics and finance for school management. | Good operational hook; expand to full SIS carefully. |

### 4.4 LMS/SIS integration

**[Verified]** Zeraki's strongest integration pattern is the loop between admission-number sync, teacher phone mark entry, analytics, parent reports, fee balance, SMS and remedial learning.

**[Recommendation]** Borrow the loop, but rebuild the data model around CBE evidence rather than marks alone.

### 4.5 Assessment and analytics

**[Verified]** Zeraki Analytics provides performance analysis by learner/class/subject and supports parent reports.

**[Claim]** Zeraki reports large-scale adoption in Kenyan secondary schools.

**[Recommendation]** Zeraki's weakness is conceptual: marks-centric reporting does not fully communicate CBE competency levels, growth, rubric evidence or SBA contribution. KLB should make this its differentiator.

### 4.6 Mobile, offline and low bandwidth

**[Verified]** Zeraki documents school LAN/TV deployment.

**[Verified]** No full offline mode in the mobile apps was documented in the sources reviewed.

**[Verified]** Bulk SMS to parents is documented; SMS learner lessons are not.

**[Recommendation]** Zeraki's LAN model is useful for school-based deployments, but KLB needs device-level offline continuity for learners moving between home and school.

### 4.7 APIs and architecture

**[Assumption]** Public developer documentation for Zeraki was not found. Treat API availability and architecture as unverified.

### 4.8 Pricing

**[Assumption]** School SaaS pricing is not public. Use procurement intelligence and pilot quotes before modelling KLB pricing.

### 4.9 Strengths and weaknesses

**Strengths [Verified]:**

- Deep Kenyan school workflow integration.
- Analytics-to-action feedback loop.
- Teacher and parent adoption surfaces.
- Admission-number and marks workflow fit Kenyan schools.

**Weaknesses [Verified/Assumption]:**

- CBE alignment is partial; content still foregrounds 8-4-4/KCSE.
- Marks-centric reporting may not communicate competencies.
- No documented full mobile offline mode.
- Pricing and APIs are opaque.

### 4.10 Five valuable concepts to borrow from Zeraki

| # | Concept | Evidence | Kenya adaptation | Added functionality | Technical need | Cost/complexity | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Admission-number-based identity sync | Verified admission-number sync | Use KNEC assessment number + school admission number + KEMIS-compatible IDs | Identity resolution across transfers and exams | Identity service, reconciliation jobs | Medium | **Adapt** |
| 2 | Teacher phone mark entry | Verified teacher phone mark entry | Convert to mobile evidence entry with rubric and SBA capture | Offline queue, validation, audit | Mobile forms, sync engine | Medium | **Adapt** |
| 3 | Analytics-to-remedial loop | Verified analytics + learning linkage | Link misconception to prescribed KLB lesson/practice | Recommendation engine | Rules engine, content tags | Medium | **Adapt** |
| 4 | Parent report with academics + fees | Verified parent reports | Add attendance, competency bands and one parent action | Explainable report | Template service, parent API | Medium | **Adapt** |
| 5 | School LAN/TV deployment | Verified LAN/TV deployment | Use for offline content caching in schools | Local content server, sync dashboard | LAN cache, device management | High | **Borrow selectively** |

---

## 5. Platform 2: ShuleSoft — deep analysis

### 5.1 Origin, users and purpose

**[Verified]** ShuleSoft is Tanzanian, based in Dar es Salaam. It is associated with ShuleSoft Limited/INETS lineage. Founder/CEO is Ephraim Solomon Swilla. The product lineage appears to predate 2022 despite the company site saying 2022. [ShuleSoft](https://shulesoft.co/)

**[Verified]** ShuleSoft was named a 2024 Mastercard Foundation EdTech Fellow. [Mastercard Foundation](https://mastercardfdn.org/)

**[Verified]** ShuleSoft is an SIS/ERP-first platform with a learning layer.

### 5.2 Modules

**[Verified]** Modules include:

- Administration/HR.
- Academic Management.
- Accounts/Finance.
- Operations — hostel, library, transport, attendance.
- Communication.
- Digital Learning/AI — AI Ask, AI Tutor, Online Exam, AI Exam Prep, Home Package.

**[Secondary]** Product pages show operational states such as hostel room occupancy, overdue library books, transport route status and attendance totals.

### 5.3 Learner, teacher, parent and admin experience

**[Verified]** ShuleSoft Parent Experience uses plain-language prompts: "This Week for Amina," "Reassurance," "One Parent Action," and tabs for Reports, Payments, Attendance. [ShuleSoft Parent Experience](https://shulesoft.co/parent-app)

**[Verified]** ShuleSoft Academic says: "Know How Every Student Is Performing Before Parents Ask," with real-time grading and instant parent report sharing. [ShuleSoft Academic](https://shulesoft.co/academic)

**[Recommendation]** The most valuable UX idea is not more dashboards; it is **one parent action** and reassurance.

### 5.4 LMS/SIS integration

**[Verified]** ShuleSoft's core architectural lesson is canonical student identity, event-driven cross-module automation, one student financial ledger, and a unified communication fabric with delivery logs.

**[Recommendation]** Build these as platform services, not module-local features.

### 5.5 Assessment, analytics and AI

**[Verified]** ShuleSoft supports grading, performance analytics, digital teaching records and online exams.

**[Verified]** AI costs are usage-based. This should be treated as a cost-control warning.

### 5.6 Mobile, offline and low bandwidth

**[Verified]** No documented offline mode.

**[Verified]** WhatsApp add-on is documented.

**[Recommendation]** Kenya adaptation must add offline-first sync and low-data modes; ShuleSoft does not solve this.

### 5.7 APIs and architecture

**[Verified]** REST APIs are claimed, but no public developer documentation was found.

**[Verified]** RBAC, audit trails and school-level rule configuration are documented.

**[Recommendation]** Borrow the governance model; verify API quality through due diligence.

### 5.8 Pricing

**[Verified]** Tanzania: TZS 10,000/student/year for all modules. Outside Tanzania: USD 5/student/year. Enterprise: USD 9.9/student/year. WhatsApp add-on: TZS 50,000/month. Attendance device: TZS 1,750,000. Bulk SMS: TZS 20. AI is usage-based. [ShuleSoft](https://shulesoft.co/)

**[Verified]** Kenya KES selector is dynamic; no fixed public KES price was found.

### 5.9 Strengths and weaknesses

**Strengths [Verified]:**

- SIS breadth.
- Strong parent communication pattern.
- Operational status surfaces.
- Module automation and central identity.

**Weaknesses [Verified/Assumption]:**

- No documented offline mode.
- No public developer docs.
- No verified named Kenyan production school.
- AI cost is variable.

### 5.10 Five valuable concepts to borrow from ShuleSoft

| # | Concept | Evidence | Kenya adaptation | Added functionality | Technical need | Cost/complexity | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Canonical student identity | Verified SIS breadth | One learner record across LMS/SIS/content | Transfer and duplicate detection | Identity service | High | **Borrow** |
| 2 | Event-driven cross-module automation | Verified module integration | Attendance/marks/fee events trigger workflows | Policy engine, event bus | Kafka/SQS-style events | High | **Adapt** |
| 3 | Unified communication fabric | Verified parent/WhatsApp/SMS patterns | One inbox with SMS/WhatsApp/email/in-app | Delivery receipts, consent | Messaging gateway | Medium | **Adapt** |
| 4 | One parent action | Verified parent experience | Plain-language weekly parent summary | Explainable reports | Parent service, templates | Low | **Borrow** |
| 5 | Guided data migration | Verified in 2025 Milango playbook | Kenyan school onboarding templates | Import validation, dry runs | ETL + data quality | Medium | **Borrow** |

**[Secondary]** A 2025 Milango playbook documented Nairobi exploration: four private schools, one payments provider, one accelerator, and a three-month pilot drafting including M-Pesa. Treat this as market exploration, not validated Kenyan demand.

---

## 6. Platform 3: Moodle — deep analysis

### 6.1 Origin, users and purpose

**[Verified]** Moodle launched in 2001, created by Martin Dougiamas. Moodle App followed in 2013, MoodleCloud in 2015, Moodle Workplace in 2019, and B Corp certification in 2021, renewed in 2025. [Moodle story](https://moodle.com/about/the-moodle-story/)

**[Verified]** Moodle is open source with no licence fees, self-hosting, data control, themes, integrations and plugins. [Moodle open source](https://moodle.com/about/open-source/)

**[Claim]** Moodle reports more than half a billion users, 3.4bn+ enrolments and 148,000+ sites. Treat as vendor-reported.

**[Verified]** Moodle core is PHP, GPL-3.0, with an active repository. [Moodle GitHub](https://github.com/moodle/moodle)

### 6.2 Purpose and users

**[Verified]** Moodle serves K–12, higher education, vocational education, business/government training through Moodle Workplace, and individual/small-team users through MoodleCloud.

### 6.3 Features

**[Verified]** Moodle supports courses, activities, assignments, quizzes, forums, workshops, SCORM, H5P, LTI, gradebooks, completion tracking, competencies, badges, reports, analytics, role-based access, themes, custom formats, mobile access and web services.

### 6.4 Learner, teacher, parent and admin experience

| Role | Verified experience |
|---|---|
| Learner | Course sections, "To do" completion lists, grades, competencies, reports, badges and app access. |
| Teacher | Activities, question banks, completion rules, restricted access, competency ratings, reports, constrained offline quizzes. |
| Parent | Configurable parent role with selected visibility such as activity reports, grades and posts; not a polished parent app. |
| Admin | Roles/capabilities in context, plugins, themes, auth, enrolments, analytics, web services and reports. |

### 6.5 Assessment and analytics

**[Verified]** Moodle quizzes support reusable question banks, detailed feedback and attempts. Analytics include descriptive, predictive, diagnostic and prescriptive models; built-in models include students at risk, upcoming activities due and no teaching. Machine-learning models need training data and model fit. [Moodle Analytics, archived](https://web.archive.org/web/20241230102303/https://docs.moodle.org/405/en/Analytics)

### 6.6 Mobile, offline and low bandwidth

**[Verified]** Moodle App free plan is €0 with 50 active push devices and 2 offline courses per device per site. Premium is €499/year with unlimited push/offline and is included with Moodle Official Hosting/MoodleCloud. [Moodle App](https://moodle.com/products/moodle-app/)

**[Verified]** Offline docs explicitly reference developing countries, rural areas, restricted data plans and shared connections. Users can download content, sections or courses. Offline quizzes are disabled by default and require no time limit, deferred feedback, sequential navigation and no network-address requirement. [Moodle offline docs, archived](https://web.archive.org/web/2025id_/https://docs.moodle.org/405/en/Moodle_app_offline_features)

**[Verified]** No dedicated quantified low-bandwidth mode was verified.

### 6.7 APIs and architecture

**[Verified]** Moodle web services use tokens; plugin types include activity modules, blocks, themes, course formats, auth, enrolment, question types, repositories, reports, ML backends and LTI services. [Moodle plugin types](https://moodledev.io/docs/5.2/apis/plugintypes)

### 6.8 Pricing

**[Verified]** Moodle core has no licence fee. MoodleCloud annual plans: Starter US$160/year for 50 users; Mini US$260 for 100; Small US$470 for 200; Medium US$1,130 for 500; Standard US$2,000 for 750. MoodleCloud explicitly disallows plugins and integrations. Moodle App Premium is €499/year. Moodle Workplace is licensed. [MoodleCloud](https://www.moodlecloud.com/standard-plans/#pricing)

### 6.9 Strengths and weaknesses

**Strengths [Verified]:**

- Architectural extensibility.
- No licence fee and data ownership.
- Granular context permissions.
- Strong offline app.
- Native competency and completion tracking.
- Reusable question banks.

**Weaknesses [Verified/Assumption]:**

- Operational and QA burden.
- MoodleCloud plugin restriction.
- Parent experience needs configuration.
- Offline quizzes have strict constraints.
- Analytics quality depends on data.

### 6.10 Five valuable concepts to borrow from Moodle

| # | Concept | Evidence | Kenya adaptation | Added functionality | Technical need | Cost/complexity | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Plugin-type taxonomy | Verified first-class plugin types | Extension points for activities, reports, question types, auth, content rules | Local language packs, KICD plugins | Modular monolith + plugin registry | High | **Borrow** |
| 2 | Roles + context permissions | Verified context-based roles | School, class, subject, activity and user contexts | Guardian consent boundaries | RBAC/ABAC | High | **Borrow** |
| 3 | Completion-driven progression | Verified completion criteria and To do lists | CBE outcome completion | Learner next-action engine | Rules engine | Medium | **Borrow** |
| 4 | Competency frameworks + learning plans | Verified native competencies | KICD competency codes | Rubric evidence, SBA rollup | Competency service | High | **Borrow** |
| 5 | Offline app with explicit constraints | Verified offline course download + quiz rules | Kenyan low-data mode | Offline-first sync with conflict rules | PWA/local DB | High | **Adapt** |

---

## 7. Platform 4: Canvas LMS — deep analysis

### 7.1 Origin, users and purpose

**[Verified]** Instructure was founded in 2008; Canvas launched in 2011. Instructure expanded internationally in 2014, reached a US$1B market cap in 2017, acquired Mastery in 2019 and Parchment in 2024, and was acquired by KKR in 2024. Headquarters are in Salt Lake City; CEO is Steve Daly. [Instructure about](https://www.instructure.com/about)

**[Verified]** Canvas core is AGPLv3 Ruby on Rails. Production docs recommend PostgreSQL 14+, Redis 6.x+ where needed, and POSIX deployment. [Canvas GitHub](https://github.com/instructure/canvas-lms)

**[Verified]** Canvas is delivered through Core, Plus and Next tiers. [Canvas tiers](https://www.instructure.com/products/canvas-tiers)

### 7.2 Features

**[Verified]** Canvas supports modules, pages, assignments, discussions, quizzes, files, SpeedGrader, rubrics, Gradebook, outcomes, Learning Mastery Gradebook, blueprints, feature settings, analytics, Canvas Data, SIS imports, grade passback, LTI 1.3, REST/JSON APIs, OAuth2, GraphQL and OpenAPI-generated docs.

### 7.3 Role experience

| Role | Verified experience |
|---|---|
| Learner | Module navigation, discussions, quizzes, grades, analytics and Student app. |
| Teacher | SpeedGrader, Gradebook, rubrics, "Message Students Who…", annotations, announcements, Inbox. |
| Parent | Canvas Parent exposes due dates, announcements, reminders and grades. |
| Admin | Blueprints, feature settings, SIS settings, analytics, reports, LTI registrations, developer keys. |

### 7.4 Assessment and analytics

**[Verified]** Canvas has a strong outcomes-to-evidence chain: rubrics aligned to outcomes, Learning Mastery summaries, filters, CSV export and Outcome Results API. [Canvas Outcome Results API](https://developerdocs.instructure.com/services/canvas/resources/outcome_results.md)

**[Verified]** Mastery is a separate K–12 product for standards-aligned assessment, item banks and reporting.

**[Verified]** No built-in high-stakes proctoring was verified; treat as integration-dependent.

### 7.5 LMS/SIS boundary

**[Verified]** Canvas supports SIS imports, SIS CSV format, terms, sections, enrolments, SIS IDs and grade passback, but remains an LMS and treats SIS as external.

### 7.6 Mobile, offline and low bandwidth

**[Verified]** Canvas has free Student, Teacher and Parent apps. Student offline mode launched in June 2024 with selected course/content downloads, automatic sync, shared-device downloads and read-only offline content. Educators can download submissions for offline grading. Offline mode is not enabled by default and real-time communication is unavailable offline. [Canvas offline press release](https://www.instructure.com/press-release/instructure-launches-offline-feature-canvas-student-app-furthering-equitable-access)

**[Verified]** No quantified low-bandwidth mode was verified.

### 7.7 APIs and architecture

**[Verified]** Canvas is API-first: REST JSON, OAuth2, GraphQL, OpenAPI, SIS APIs and LTI 1.3.

### 7.8 Pricing

**[Verified]** Pricing is quote-based; no public per-seat price was found on official tier pages.

**[Verified]** Canvas Lite was announced 9 September 2026 and went live 30 September 2026. It is free worldwide, US-hosted, 500MB/course, with no course analytics, attendance tracking or full API access tokens. [Canvas Lite press release](https://www.instructure.com/press-release/instructure-announces-canvas-lite-new-free-course-tool-built-educators)

### 7.9 Strengths and weaknesses

**Strengths [Verified]:**

- Polished educator workflows.
- Module-based course structure.
- Strong feedback and rubric system.
- Outcomes/mastery chain.
- API-first design.
- Parent app.

**Weaknesses [Verified/Assumption]:**

- Quote-based pricing.
- Free tier is limited.
- Not a full SIS.
- Offline is constrained and admin-enabled.
- Open source does not mean free hosted service.

### 7.10 Five valuable concepts to borrow from Canvas

| # | Concept | Evidence | Kenya adaptation | Added functionality | Technical need | Cost/complexity | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Modules as course spine | Verified module structure | KICD-aligned modules by strand/outcome | Offline lesson packs | Content model, packaging | Medium | **Borrow** |
| 2 | SpeedGrader-style grading | Verified single-pane grading | Mark SBA evidence and assignments offline | Audio feedback, rubrics | Grading UI, media storage | Medium | **Borrow** |
| 3 | Outcome → rubric → mastery | Verified Outcome Results API and mastery gradebook | Map to KICD competency codes | CBE report cards | Competency service | High | **Borrow** |
| 4 | Criteria-based messaging | Verified "Message Students Who…" | Reach learners by misconception/attendance/risk | SMS/in-app escalation | Rules + messaging | Medium | **Borrow** |
| 5 | Blueprint courses | Verified blueprint feature | Roll out KLB master courses to all schools | Versioned publishing | Publishing pipeline | High | **Borrow** |

---

## 8. Platform 5: Eneza Education / Shupavu291 — deep analysis

### 8.1 Origin, users and purpose

**[Verified]** Eneza was founded in 2011/2012 as MPrep by Toni Maraviglia and Kago Kagichiri. Wambura Kimunyu became CEO in 2019. [Eneza-related sources](https://enezaeducation.com/)

**[Verified]** "Shupavu291" combines "Shupavu" meaning champion/confident with `*291#`. The exact phrase "Shupavu wa Shupavu" was not verified.

**[Verified]** Eneza's purpose is low-cost, basic-phone-accessible revision and tutoring.

### 8.2 Access model and features

**[Verified]** Learners dial `*291#` or send `LEARN` to `20851`. USSD registration captures name, class and baseline. Lessons are delivered as roughly three SMS messages plus five escalating quiz questions with explanatory feedback. Ask-A-Teacher sends questions to `20851` with a 5–10 minute target response. Offline Wikipedia and dictionary are included. About 99% of users use SMS. [HundrED](https://hundred.org/en/innovations/shupavu291-an-e-learning-platform-that-can-be-accessed-offline-on-basic-feature-phones-through-sms) · [Engineering for Change](https://engineeringforchange.org/solutions/product/eneza-education)

**[Verified]** Pricing reported includes airtime micropayments of about US$0.03/day, US$0.15/week, US$0.50/month, or KES10/week. [Engineering for Change](https://engineeringforchange.org/solutions/product/eneza-education)

### 8.3 Evidence caution

**[Claim]** Reach figures such as 12m+ learners are reported by HundrED and other sources but vary.

**[Secondary]** Independent BJET/Kizilcec and Chen research found no evidence of enhanced learning gains from Shupavu291 use. This is critical: Eneza is an access innovation, not a proven learning-outcome innovation.

### 8.4 Strengths and weaknesses

**Strengths [Verified]:**

- Zero-friction basic-phone access.
- Very low cost.
- Short feedback loops.
- Teacher question escalation.
- Offline reference material.

**Weaknesses [Verified/Secondary]:**

- SMS is constrained for rich CBE evidence and collaboration.
- Learning-impact evidence is mixed.
- Reach figures conflict.
- Not a full school system.

### 8.5 Five valuable concepts to borrow from Eneza

| # | Concept | Evidence | Kenya adaptation | Added functionality | Technical need | Cost/complexity | Decision |
|---|---|---|---|---|---|---|---|
| 1 | USSD/SMS zero-friction onboarding | Verified `*291#` and `LEARN` flow | Basic-phone revision and parent notifications | USSD menu for low-data learners | Africa's Talking USSD/SMS | Medium | **Adapt** |
| 2 | Micro-lesson SMS sequence | Verified 3 SMS + 5 questions | CBE micro-revision by outcome | Adaptive follow-up | Content converter, SMS gateway | Medium | **Adapt** |
| 3 | Immediate explanatory feedback | Verified quiz feedback | Explain why answer is right/wrong | Misconception tagging | Item bank, rules | Medium | **Borrow** |
| 4 | Ask-A-Teacher | Verified `20851` teacher flow | Escalate to teacher/tutor with SLA | Queue, privacy, triage | Messaging workflow | Medium | **Adapt** |
| 5 | Offline reference | Verified offline Wikipedia/dictionary | KLB glossary and formula bank offline | Local packaged reference | Content packager | Low | **Borrow** |

---

## 9. Platform comparison matrix

| Dimension | Zeraki | ShuleSoft | Moodle | Canvas | Eneza |
|---|---|---|---|---|---|
| Origin | Kenya, Litemore, 2014/15 | Tanzania, INETS/ShuleSoft lineage | Global, 2001, Martin Dougiamas | US, Instructure, 2008/2011 | Kenya/Africa, 2011/12 as MPrep |
| Primary identity | School analytics + learning | SIS/ERP + learning | Open LMS | Commercial LMS | SMS/USSD learning |
| Main users | Secondary schools, teachers, parents, learners | Schools, admins, parents, teachers | Schools, universities, trainers, learners | K–12, higher ed, educators, parents | Basic-phone learners |
| LMS depth | Medium | Medium | Very high | Very high | Low/medium |
| SIS depth | Medium | Very high | Low | Low | None |
| Assessment | Marks, quizzes, exams, analytics | Grading, online exams, analytics | Quizzes, question banks, competencies | Rubrics, outcomes, mastery | SMS quizzes, feedback |
| Analytics | Strong school performance analytics | Performance + operations | Descriptive/predictive/diagnostic/prescriptive | Admin analytics + Canvas Data | Limited reported |
| CBE alignment | Partial, KCSE heritage | Not Kenya-specific | Competency framework generic | Outcomes/mastery generic | Revision-oriented |
| Offline | School LAN/TV; no verified full mobile offline | No documented offline | Strong app offline, constrained quizzes | Read-only content offline, admin-enabled | SMS is inherently offline-tolerant |
| Mobile | Android/web | Parent app, operations apps | App + responsive web | Student/Teacher/Parent apps | Basic phone, SMS/USSD, Android/web |
| APIs | Unverified public docs | REST claimed, no public docs | Web services + plugins | REST, GraphQL, OAuth2, LTI | Unverified |
| Architecture | Unknown | Modular SIS | PHP plugin-first | Ruby/Rails API-first | Unknown |
| Pricing visibility | Not public | Public non-Kenya prices | Open core + cloud prices | Quote-based | Micropayment/KES10 week reported |
| Main strength | Kenyan school workflow fit | Integrated operations | Extensibility and offline | UX and outcomes chain | Access at bottom of pyramid |
| Main constraint | Marks-centric, partial CBE | No offline, Kenya unproven | Ops burden | Cost and no SIS | Weak learning evidence |

---

## 10. Borrow / Adapt / Avoid matrix

| Source | Concept | Decision | Rationale |
|---|---|---|---|
| Zeraki | Admission-number sync | **Adapt** | Useful, but extend to KNEC/KEMIS identity. |
| Zeraki | Teacher phone mark entry | **Adapt** | Move from marks to evidence/SBA. |
| Zeraki | Analytics-to-remedial loop | **Adapt** | Strong idea; needs CBE content mapping. |
| Zeraki | Parent report with fee balance | **Adapt** | High-value parent hook; add competency explanation. |
| Zeraki | Marks-centric school analytics | **Avoid** | Insufficient for CBE. |
| ShuleSoft | Canonical student identity | **Borrow** | foundational. |
| ShuleSoft | Event-driven cross-module automation | **Adapt** | Need Kenyan policy configurability. |
| ShuleSoft | Unified communication fabric | **Adapt** | Must include consent and delivery logs. |
| ShuleSoft | One parent action | **Borrow** | Excellent restraint. |
| ShuleSoft | No-offline assumption | **Avoid** | Fails Kenyan context. |
| Moodle | Plugin taxonomy | **Borrow** | Strong extensibility pattern. |
| Moodle | Roles-in-context | **Borrow** | Needed for schools and guardians. |
| Moodle | Completion rules | **Borrow** | Fits CBE progression. |
| Moodle | Competencies | **Borrow** | Core differentiator. |
| Moodle | Self-hosting without ops model | **Avoid** | KLB needs managed service. |
| Canvas | Modules as course spine | **Borrow** | Clear and teachable. |
| Canvas | SpeedGrader workflow | **Borrow** | Strong teacher productivity pattern. |
| Canvas | Outcome → rubric → mastery | **Borrow** | Essential. |
| Canvas | Parent app bounded visibility | **Borrow** | Clear design boundary. |
| Canvas | Quote-only pricing and no SIS | **Avoid** | Procurement and ecosystem mismatch. |
| Eneza | USSD/SMS access | **Adapt** | Valuable fallback, not primary LMS. |
| Eneza | Micro-lessons + immediate feedback | **Borrow** | Strong low-data pattern. |
| Eneza | Ask-A-Teacher | **Adapt** | Add Teacher SLA and safeguarding. |
| Eneza | Learning-gain claims | **Avoid** | Independent evidence does not support copying claims. |

---

## 11. Integrated ecosystem concept: LMS + SIS + publishing

### 11.1 One ecosystem, not three products

**[Recommendation]** The three components should share:

- identity and access;
- school and learner records;
- curriculum and competency taxonomy;
- content identifiers and versioning;
- assessment events;
- messaging and notifications;
- analytics and reporting;
- audit logs and privacy controls.

### 11.2 Domain boundaries

| Domain | System of record | Consumes | Publishes |
|---|---|---|---|
| Identity | IAM/people service | KEMIS-like IDs, school records | User, role, guardian link |
| Student records | SIS | Admissions, transfers | Learner, enrolment, class, guardian |
| Curriculum/content | Publishing platform | KICD curriculum versions | Learning objects, versions, licences |
| Learning activity | LMS | Content, enrolment | Progress, submissions, evidence |
| Assessment | LMS/assessment service | Item bank, rubrics, SBA config | Scores, mastery, feedback |
| Finance | SIS/finance | Fee structures, payments | Invoices, balances |
| Messaging | Communication service | All domains | Delivery logs |
| Analytics | Data platform | Events from all domains | Dashboards, alerts |

### 11.3 Curriculum-to-evidence chain

**[Recommendation]** This is the core intellectual property of the ecosystem:

1. KICD curriculum version and code.
2. KLB learning object aligned to outcome/competency.
3. Teacher assigns learning object.
4. Learner interacts, including offline.
5. Assessment item or rubric captures evidence.
6. Mastery status is calculated.
7. Growth is measured over time.
8. Teacher receives actionable triage.
9. Parent receives an explanation and one action.
10. School/board receives curriculum coverage and learning evidence.

---

## 12. Recommended modules

### 12.1 Phase 1 — foundation

- Identity and access.
- School/learner/teacher/guardian records.
- Classes and enrolment.
- Attendance.
- Timetable.
- Content library.
- Lesson delivery.
- Assignments and quizzes.
- Rubric-based evidence capture.
- Parent communication.
- Offline PWA.
- Basic analytics.
- Audit and consent management.

### 12.2 Phase 2 — differentiation

- CBE competency framework and learning plans.
- SBA workflow.
- KICD-aligned publishing workflow.
- Item bank and question bank.
- Mastery gradebook.
- Analytics-to-remediation recommendations.
- Bulk SMS/USSD fallback.
- Fee balance and payments.
- Teacher workload and curriculum coverage.
- Multi-school/group views.

### 12.3 Phase 3 — scale

- Advanced analytics and data warehouse.
- External LTI/tool marketplace.
- KEMIS-compatible reporting.
- TVET/university pathways.
- Native apps where justified.
- AI tutor with strict boundaries.
- Content marketplace and licensing.
- Advanced offline school server.

### 12.4 Feature prioritisation matrix

| Feature | User value | Differentiation | Technical complexity | Compliance need | Priority |
|---|---:|---:|---:|---:|---|
| Offline lesson + sync | Very high | Very high | High | Medium | P0 |
| Identity/enrolment | Very high | Medium | High | High | P0 |
| Attendance | Very high | Medium | Medium | High | P0 |
| Assignments/quizzes | Very high | Medium | Medium | Medium | P0 |
| Rubric/SBA evidence | High | Very high | High | High | P0/P1 |
| Parent one-action summary | High | High | Low | High | P0 |
| KICD content pipeline | High | Very high | High | Very high | P0/P1 |
| Mastery gradebook | High | Very high | High | Medium | P1 |
| Fee balance | High | Medium | Medium | High | P1 |
| SMS/USSD fallback | High | High | Medium | Medium | P1 |
| Analytics-to-remediation | High | Very high | High | Medium | P1 |
| Library/transport/hostel | Medium | Medium | High | Medium | P2 |
| AI tutor | Medium | Low/uncertain | Very high | Very high | P3 |
| Native apps | Medium | Low | High | Medium | P3 |

---

## 13. Offline-first and mobile-first strategy

### 13.1 Principles

**[Verified]** MDN documents service workers, Cache API, Background Sync/Fetch and IndexedDB as core offline web capabilities, with limitations including permissions and storage eviction. [MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation)

**[Verified]** web.dev recommends telling users their offline state, remaining actions, when connectivity improves, what is available offline, and actual data cost. [web.dev](https://web.dev/articles/offline-ux-design-guidelines)

**[Recommendation]** Product rules:

1. Offline is the default assumption, not an exception.
2. Every write action has saved, syncing, synced, failed and conflict states.
3. Never silently discard learner or teacher work.
4. Show data cost before large downloads.
5. Preserve data across sessions and devices where possible.
6. Use plain language: "Saved on this device — will sync."

### 13.2 Sync model

| Data | Offline write allowed? | Conflict rule |
|---|---|---|
| Lesson progress | Yes | Last event with device timestamp; dedupe by event ID |
| Quiz responses | Yes | Preserve attempt; sync once; server validates |
| Teacher marks | Yes | Require explicit review on conflict |
| Attendance | Yes | Require teacher confirmation on conflict |
| Fee payments | No/sms confirmation | Server authoritative |
| Safeguarding notes | Restricted | Server authoritative, minimal local cache |
| Content packs | Read-only | Versioned replacement |

### 13.3 PWA versus native

| Option | Advantages | Limits | Decision |
|---|---|---|---|
| PWA | One codebase, low install friction, offline APIs, works on low-cost Android | iOS limitations, storage eviction, device APIs vary | **Default** |
| Flutter | Strong cross-platform UI, offline DB options | Native build/release overhead, larger app size | **Only for device programmes** |
| React Native | JS ecosystem, native modules | Upgrade complexity, performance variance | **Evaluate if partner requires** |
| SMS/USSD | Basic phone reach, no data | Low richness, cost per message, privacy limits | **Fallback channel** |

### 13.4 Data cost and compression

**[Verified]** Save-Data client hints allow lighter applications; responsive images and lazy loading reduce payloads. [web.dev Save-Data](https://web.dev/articles/optimizing-content-efficiency-save-data) · [MDN Lazy loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Lazy_loading)

**[Recommendation]** Build text-first content packs, compressed media, optional HD downloads, lazy-loaded images, and a "light mode" that preserves core function.

---

## 14. Technology stack and architecture

### 14.1 Recommended stack

| Layer | Recommendation | Rationale |
|---|---|---|
| Backend | Django 6.x + DRF | Mature, secure defaults, admin, ORM, strong API ecosystem |
| Language | Python 3.12+ or 3.13 LTS-style choice | DRF supports Python 3.10–3.15 |
| Database | PostgreSQL 19 | ACID, JSONB, full-text search, RLS, replication, PITR |
| Cache/queue | Redis + Celery or durable queue | Background sync, notifications, reports |
| Search | PostgreSQL FTS initially; OpenSearch later if needed | Avoid premature complexity |
| Web frontend | React/Next.js | Component system, PWA support |
| Offline store | IndexedDB with Dexie/PouchDB-style layer; SQLite for native | Mature local persistence |
| API style | REST + OpenAPI; GraphQL only where needed | Interoperability and docs |
| Events | Domain events via durable broker | Decouple LMS/SIS/publishing |
| Storage | S3-compatible object storage | Media and content packs |
| Hosting | Cape Town AWS region initially; Nairobi region if requirements emerge | Lower latency than Europe |
| Messaging | Africa's Talking SMS/USSD + email/WhatsApp where allowed | Kenya channel fit |
| Observability | OpenTelemetry, structured logs, metrics, traces | Operational readiness |
| Identity | OIDC/OAuth2, RBAC/ABAC, consent service | Schools and guardians |

### 14.2 Why not simply fork Moodle or Canvas?

**[Verified]** Moodle and Canvas are open source at core but encode assumptions, upgrade paths and extension models that would constrain a tightly integrated publishing/SIS product.

**[Recommendation]** Borrow their concepts, not their codebases, unless a pilot proves a fork is cheaper over five years. A fork creates upgrade risk, plugin QA burden and licensing complexity.

### 14.3 Hosting and cost

**[Verified]** AWS has no Kenya region. `af-south-1` Cape Town is available and is an opt-in region. AWS Outposts is supported in Kenya. Cognito multi-region replication includes Cape Town. [AWS](https://aws.amazon.com/)

**[Secondary]** Cape Town is 17.4–25% more expensive than Ireland for comparable services, with egress about 71% higher. Nairobi latency to Cape Town is around 85ms versus 191ms to Frankfurt and 200ms to Ireland.

**[Secondary]** Kenyan software engineer average salary of KSh 180,000/month is a third-party figure. Employer costs include NSSF, SHIF and housing levy.

**[Recommendation]** Model three hosting scenarios:

1. Cape Town managed cloud — fastest launch.
2. Local data-centre/colo — data-residency and latency option.
3. Hybrid — core cloud plus school/local caches.

### 14.4 Messaging costs

**[Verified]** Africa's Talking pricing includes Safaricom bulk SMS at KES 0.8/0.7/0.6/0.4 by volume; sender ID setup KES 14,100 bundled; shared USSD KES 10,000–40,000/month; prepaid USSD end-user KES 1 + KES 0.25 infra fee; dedicated Safaricom USSD setup KES 145,000 and monthly KES 58,000–70,000; short code KES 15,000/month per telco or shared KES 2,000/month + KES 5,000 setup. [Africa's Talking](https://africastalking.com/)

**[Recommendation]** Do not make SMS the primary delivery channel. Use it for high-value alerts and fallback.

### 14.5 Architecture diagram — textual

```
Learner/Teacher/Parent/Admin devices
  PWA | SMS/USSD | optional native | school LAN cache
        |
  API gateway / CDN / WAF
        |
  Django REST API services
  |-- IAM & consent
  |-- SIS/student records
  |-- LMS/courses/assessment
  |-- Publishing/content
  |-- Messaging
  |-- Analytics/events
        |
  PostgreSQL primary + read replicas + object storage + Redis/queue
        |
  Data warehouse/reporting + KEMIS exports + school dashboards
```

---

## 15. Distinctive UI/UX strategy

### 15.1 Design thesis

**[Recommendation]** A role-aware, text-first learning operations ecosystem: one design system, four role shells, calm school-ready visual language, no generic AI dashboard aesthetics.

**[Verified]** Eneza proves text-first access; Canvas and Moodle provide dashboard and course-navigation patterns; ShuleSoft provides parent reassurance and operational status; WCAG 2.2, NN/g, Material Design and Apple HIG provide usable interaction principles.

### 15.2 Role dashboards

| Role | Primary question | First screen |
|---|---|---|
| Learner | "What should I do next, and how am I improving?" | Continue lesson, due task, mastery status, offline status |
| Teacher | "Who needs help, and what should I teach next?" | Assignments to mark, learners needing support, topic heatmap |
| Parent | "Is my child okay, and what should I do?" | This week summary, one parent action, attendance, recent result |
| Admin | "Where are the operational and learning risks?" | Attendance, coverage, assessment completion, teacher activity, alerts |

### 15.3 Navigation

**[Verified]** Material Design recommends 3–5 phone tabs, 3–7 tablet rail destinations and drawers for larger screens. Apple HIG says tab bars preserve navigation state and are for top-level sections. [Material Design](https://m3.material.io/components/navigation-bar) · [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/tab-bars.md)

**[Recommendation]:**

- Phone learner: Home, Learn, Practice, Progress, Offline.
- Phone teacher: Today, Classes, Assignments, Insights, Messages.
- Phone parent: Home, Reports, Attendance, Payments, Help.
- Phone admin: Overview, People, Learning, Operations, Reports.
- Desktop: persistent grouped sidebar.

### 15.4 Progress visualisation

**[Verified]** Getting Smart distinguishes mastery status from mastery progress; Springer research describes linked mastery status and growth visuals; Edutopia documents visual rubrics. [Getting Smart](https://www.gettingsmart.com/2019/10/16/using-mastery-data-to-measure-growth-in-student-learning/) · [Springer](https://link.springer.com/chapter/10.1007/978-3-031-16290-9_48) · [Edutopia](https://edutopia.org/article/representing-proficiency-progress-visual-rubrics)

**[Recommendation]** Use three layers:

1. Status: `Fractions — Developing`.
2. Growth: `3 new skills mastered this month`.
3. Next action: `Practice unlike denominators — 5 questions`.

Avoid logins, time in app, videos watched, generic engagement scores and public leaderboards as primary signals.

### 15.5 Visual identity

**[Verified]** The Smithsonian documents the kanga's `pindo` border, `mji` central design and `jina` written message. [Smithsonian](https://festival.si.edu/blog/2014/a-cloth-of-many-meanings-the-khangas-role-in-kenyan-culture)

**[Recommendation]** Use kanga structure, not kanga wallpaper:

- thin semantic border on achievement/subject surfaces;
- restrained central motif per subject/level;
- short bilingual microcopy;
- deep ink/forest green, warm cream, clay/terracotta, ochre, river blue/teal;
- open-licensed African-language typography such as Questrial, Judson, Agbalumo and Noto.

**[Verified]** Questrial, Judson and Agbalumo are available under SIL Open Font License 1.1. [Google Fonts](https://fonts.google.com/)

**[Recommendation]** Avoid purple AI gradients, glassmorphism, robot mascots, neon donut charts, safari clichés, decorative card grids and low-contrast pastels.

### 15.6 Accessibility

**[Verified]** WCAG 2.2 AA includes non-text alternatives, captions, semantics, orientation, use of colour, contrast, resize text, reflow, non-text contrast, text spacing, keyboard access, focus order, focus visible, target size, reading level, consistent help, redundant entry, accessible authentication and status messages. [W3C WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)

**[Verified]** KICTANet frames accessibility to public ICT as a civil right and recommends WCAG-based compliance. [KICTANet](https://kictanet.or.ke/accessibility-101-guidelines-for-organisational-compliance)

**[Recommendation]** Release gate: WCAG 2.2 AA, contrast checks, keyboard-only testing, screen-reader smoke tests, reflow at 320px, target sizes, captions, and plain-language review.

---

## 16. Compliance, privacy, safeguarding, and accessibility

### 16.1 Data protection

**[Verified]** Data Protection Act Cap. 411C Section 33 requires parent/guardian consent for child data. The General Regulations are LN 263/2021 and Registration Regulations LN 265/2021. [Kenya Law](https://kenyalaw.org/)

**[Verified]** ODPC guidance includes Education Sector Guidance (Dec 2023), Children's Data Guidance (adopted 6 Nov 2025), and AI Guidance (July 2026). Enforcement examples include Nairobi Academy and Alphax Academy. [ODPC](https://www.odpc.go.ke/)

**Recommendation:**

- DPIA before pilot.
- Verifiable guardian consent.
- Data minimisation.
- Purpose limitation.
- Retention/deletion schedules.
- Rights request workflow.
- Child-friendly privacy notices.
- Role-based access and audit logs.
- No advertising to children.
- No third-party AI training on learner data.

### 16.2 Curriculum compliance

**[Verified]** KICD Act Cap. 211A Section 27 makes unapproved curriculum materials in covered institutions an offence. KICD standards cover digital course materials, educational mobile apps and LMS/e-distribution platforms. [Kenya Law](https://kenyalaw.org/) · [KICD](https://kicd.ac.ke/)

**Recommendation:**

- Approval-status workflow for every content item.
- Version locking by term/year.
- Submission/export package for KICD review.
- Avoid claiming KICD approval without current documentation.

### 16.3 Copyright and licensing

**[Verified]** Copyright Act Cap. 130 is relevant to digital textbooks. [Kenya Law](https://kenyalaw.org/)

**Recommendation:**

- Rights metadata on every asset.
- School, term, per-learner and offline-download licences.
- Expiry and Revocation.
- Watermarking where appropriate.
- Clear fair-use and accessibility-exception policy.

### 16.4 Accessibility compliance

**[Verified]** KS 2952-1:2022 and KS 2952-2:2022; KICD app standards require alt text, voiceover, larger/bold text and disability adaptation. [KEBS](https://www.kebs.org/) · [KICD](https://kicd.ac.ke/)

**Recommendation:** treat WCAG 2.2 AA as the engineering baseline, then add Kenya-specific KS/KICD checks.

---

## 17. KLB opportunity and positioning

### 17.1 Why KLB can win

| KLB asset | Strategic use |
|---|---|
| Government ownership | Trust with MoE, KICD and public schools |
| Publishing history | Content authority and rights management |
| KLB Act digital/e-material mandate | Legal/institutional fit |
| Existing channels | Distribution through schools and partners |
| KICD relationship | Approval workflow and curriculum alignment |
| Brand recognition | Parent and teacher trust |

### 17.2 What KLB must not do

- Do not compete as a cheap generic LMS.
- Do not lead with PDFs.
- Do not claim KICD approval without documentation.
- Do not build four disconnected apps.
- Do not make AI the headline before curriculum, privacy and evidence are solved.
- Do not assume capitation can be invoiced without procurement readiness.
- Do not copy Zeraki, ShuleSoft, Moodle, Canvas or Eneza interfaces.

### 17.3 Positioning statement

**[Recommendation]**

> KLB One Learning is the trusted Kenyan learning ecosystem that connects curriculum-approved content, school operations, assessment evidence and parent communication in one offline-first platform — so every learner's progress is understandable, actionable and aligned to CBE.

---

## 18. Roadmap and implementation plan

### 18.1 0–3 months: validate

- Confirm KLB current platform inventory.
- Validate FY2024–FY2026 financials.
- Confirm KICD approval status of KLB digital assets.
- Map contracts and data flows with schools/government.
- Run discovery in at least two contrasting Kenyan contexts.
- Define four role contracts.
- Produce DPIA outline.
- Model unit economics.

### 18.2 3–9 months: foundation pilot

- Build identity, school/learner records, classes, attendance.
- Build content library and lesson delivery.
- Build assignments/quizzes and rubric evidence.
- Build offline PWA.
- Pilot in a small set of schools.
- Instrument weekly active users, sync success, support tickets and learning evidence.

### 18.3 9–18 months: differentiation

- Competency framework and learning plans.
- SBA workflow.
- Mastery gradebook.
- KICD publishing workflow.
- Parent one-action summaries.
- SMS/USSD fallback.
- Analytics-to-remediation.
- Procurement pack for public schools.

### 18.4 18–36 months: scale

- Multi-school/group dashboards.
- KEMIS-compatible reporting.
- TVET/university pathways.
- Native apps only where justified.
- Content marketplace.
- Advanced analytics.
- AI tutor only after safety and privacy approval.

### 18.5 Roadmap gates

| Gate | Evidence required |
|---|---|
| Pilot go/no-go | Teacher weekly use, learner task completion, sync reliability, parent engagement |
| Public procurement readiness | Pricing, DPIA, accessibility, security, support SLA, KICD documentation |
| Scale | Retention, renewals, cost-to-serve, content approval throughput, support load |
| AI release | Pedagogical safety review, child-data controls, bias evaluation, human escalation |

---

## 19. Commercial model

### 19.1 Pricing principles

**[Verified]** Global publisher evidence shows a shift to embedded courseware/subscriptions/inclusive access rather than isolated PDFs. McGraw Hill Q2 FY2026 revenue was US$213m, with digital at US$186.2m. Oxford reported 46% digital revenue. [Publisher financial reports](https://www.mcgrawhill.com/)

**[Verified]** Snapplify licensing guidance: one-year licences are 30–50% below eRRP, three-year licences about 20% below, and perpetual licences 0–20% below; K–12 favours one-year licences. [Snapplify](https://snapplify.com/)

**[Recommendation]:**

- Separate platform fee from content licence.
- Use per-school annual bands with per-learner caps.
- Offer termly payment for public schools.
- Offer a subsidised public-school tier.
- Offer a low-cost basic-phone revision tier.
- Avoid perpetual licences for fast-changing CBE content.
- Price support and onboarding explicitly.

### 19.2 Reference price anchors

| Product | Verified price |
|---|---:|
| MoodleCloud Starter | US$160/year, 50 users |
| MoodleCloud 100 users | US$260/year |
| MoodleCloud 200 users | US$470/year |
| MoodleCloud 500 users | US$1,130/year |
| MoodleCloud 750 users | US$2,000/year |
| ShuleSoft Tanzania | TZS 10,000/student/year |
| ShuleSoft outside Tanzania | USD 5/student/year |
| ShuleSoft Enterprise | USD 9.9/student/year |
| uLesson | ₦12,000/3 months; ₦25,000/year; ₦40,000/2 years; ₦50,000/3 years |
| Snapplify Access | US$0/US$10/US$5 per school tiers |
| Eneza | about KES10/week reported |

**[Recommendation]** Do not copy these prices. They are anchors. Kenya capitation, procurement, school size, support burden and content rights determine the actual model.

### 19.3 Retention

**[Secondary]** Retention comes from embedded workflow — registers, attendance, marks, report cards and parent communication — not content novelty.

**[Recommendation]** Instrument weekly active teachers, weekly active learners, parent action completion, assignment/feedback loop time, offline usage, renewals, support tickets and cost-to-serve.

---

## 20. Risks and mitigations

| Risk | Severity | Evidence | Mitigation |
|---|---|---|---|
| CBE model changes | High | Verified transition timeline | Configurable assessment/competency model |
| KICD approval delays | High | Verified approval regime | Parallel approval workflow; stage content releases |
| Child-data breach | Critical | Verified DPA and ODPC guidance | DPIA, consent, minimisation, audit, encryption |
| Low teacher adoption | High | MoE reports low ICT integration | Embed in registers/marks/report cards; contextual help |
| Connectivity failure | High | CA urban/rural data | Offline-first, SMS fallback, local caching |
| Device cost | High | 8.8% household computer ownership | Phone-first and shared-device support |
| Procurement delays | High | e-GP migration | Procurement pack, termly pricing |
| Content rights conflict | Medium/high | Copyright Act | Rights metadata and licence engine |
| AI harm/privacy | High | ODPC AI guidance July 2026 | Delay AI; human escalation; no training on child data |
| Vendor lock-in | Medium | AWS no Kenya region | Portable storage, open APIs, data export |
| Cost overrun | High | Salary/cloud cost evidence | Phased build, managed PWA first |
| Marks-centric regression | Medium | Zeraki pattern | Competency-first reporting |
| Parent misunderstanding | Medium | CBE complexity | Plain-language explanations and one action |
| Accessibility failure | High | KS/WCAG/KICD standards | Release gate and audits |

---

## 21. Final recommendations and open questions

### 21.1 Final recommendations

1. **Position KLB as the CBE content-and-evidence ecosystem, not as another LMS.**
2. **Build one platform with three connected components: LMS, SIS and publishing.**
3. **Make the curriculum-to-evidence chain the core differentiator.**
4. **Adopt offline-first PWA as the default client; add native apps only when justified.**
5. **Use Django/DRF/PostgreSQL/React as the initial stack.**
6. **Implement KICD approval, child consent, accessibility and audit as platform services.**
7. **Design role-specific dashboards from one component system.**
8. **Treat SMS/USSD as a fallback channel, not the main learning experience.**
9. **Borrow Moodle's extensibility and Canvas's workflow polish; do not fork either.**
10. **Pilot in contrasting Kenyan contexts before scaling.**
11. **Separate platform, content and support revenue.**
12. **Delay AI until privacy, pedagogy and escalation are solved.**

### 21.2 Open questions that must be answered

1. What is KLB's current inventory of platforms, licences, contracts and digital assets?
2. Which KLB digital materials currently have valid KICD approval?
3. What are the audited FY2024–FY2026 financials?
4. What contracts and data flows exist with MoE, KICD, schools and partners?
5. Can KLB secure data-residency approval or is Cape Town hosting acceptable?
6. Which school segments are the beachhead: public junior/senior, private, TVET, or mixed?
7. Who pays: MoE, school, parent, donor, or a blended model?
8. What is the realistic support model for low-connectivity schools?
9. Which local languages are required by county and level?
10. What SBA evidence formats do KNEC and KICD expect in digital form?
11. Is a native app required by any device programme?
12. What accessibility conformance evidence is required for procurement?

### 21.3 Decision

**[Recommendation]** Proceed to a funded discovery and pilot phase. Do **not** proceed directly to full build. The next decision point should be based on evidence from:

- KLB asset/contract audit;
- KICD and ODPC compliance review;
- two contrasting school-context pilots;
- pricing and procurement validation;
- technical proof of offline sync and content packaging.

If those gates pass, KLB has a credible path to pioneer a distinctly Kenyan learning ecosystem that is curriculum-aligned, offline-capable, evidence-rich and commercially defensible.

---

## Appendix A: User journeys

### A.1 Learner journey — offline-first

1. Learner opens PWA on low-cost phone.
2. Sees: `Continue: Fractions — 12 min`.
3. Downloads lesson pack: `About 6 MB`.
4. Goes offline.
5. Completes lesson and quiz.
6. App shows: `Saved on this device — will sync`.
7. Reconnects.
8. App shows: `Synced at 08:40`.
9. Mastery updates: `Fractions — Developing`.
10. Next action appears: `Practice unlike denominators — 5 questions`.

### A.2 Teacher journey — evidence capture

1. Teacher opens `Today`.
2. Sees three assignments awaiting review and five learners needing support.
3. Opens a learner's evidence drawer.
4. Reviews quiz, rubric score and teacher note.
5. Marks rubric criterion offline.
6. Sends `Assign practice` and optional parent message.
7. On reconnect, conflict check runs.
8. Class mastery heatmap updates.

### A.3 Parent journey — one action

1. Parent receives SMS: `This week for Amina: 4/5 days attended. One action: sign permission note.`
2. Opens parent app or USSD.
3. Sees attendance, recent result and teacher message.
4. Reads explanation: `Developing means Amina is close but needs more practice.`
5. Completes one action.
6. Receives confirmation.

### A.4 Admin journey — school operations

1. Admin opens `Overview`.
2. Sees attendance dip in Grade 8, low assignment completion in mathematics, and 12 unsynced devices.
3. Drills into class and teacher view.
4. Reviews curriculum coverage.
5. Assigns corrective action.
6. Exports termly report.

### A.5 Content publisher journey — KICD alignment

1. Author creates learning object.
2. Tags subject, level, strand, outcome and competency.
3. Links assessment item and rubric.
4. Submits for internal review.
5. KICD approval reference and version are attached.
6. Content pack is published to selected schools.
7. Usage and evidence analytics are monitored.
8. New version supersedes old version by term.

---

## Appendix B: Master source list

### Kenya and KLB

- [Kenya Literature Bureau](https://klb.co.ke/)
- [KLB FY2022/23 financial statements — Treasury](https://treasury.go.ke/sites/default/files/financial%20statements/Kenya-Literature-Bureau-2022_2023.pdf)
- [Kenya Law](https://kenyalaw.org/)
- [KICD](https://kicd.ac.ke/)
- [KNEC](https://www.knec.ac.ke/)
- [Ministry of Education](https://www.education.go.ke/)
- [Communications Authority of Kenya](https://ca.go.ke/)
- [ODPC](https://www.odpc.go.ke/)
- [KEBS](https://www.kebs.org/)
- [Treasury/e-GP](https://www.treasury.go.ke/)

### Platforms

- [Zeraki](https://zeraki.app)
- [Zeraki Learning](https://zeraki.app/zeraki-learning)
- [Zeraki Analytics](https://zeraki.app/zeraki-analytics)
- [Zeraki parent performance article](https://zeraki.app/post/parents-now-able-monitor-learner-s-perfomance-in-new-app)
- [Acumen Zeraki profile](https://acumen.org/)
- [ShuleSoft](https://shulesoft.co/)
- [ShuleSoft Operations](https://shulesoft.co/operation)
- [ShuleSoft Digital Learning](https://shulesoft.co/digital)
- [ShuleSoft Parent Experience](https://shulesoft.co/parent-app)
- [ShuleSoft Academic](https://shulesoft.co/academic)
- [Moodle](https://moodle.com/)
- [Moodle open source](https://moodle.com/about/open-source/)
- [Moodle plugin types](https://moodledev.io/docs/5.2/apis/plugintypes)
- [Moodle App](https://moodle.com/products/moodle-app/)
- [MoodleCloud pricing](https://www.moodlecloud.com/standard-plans/#pricing)
- [Moodle GitHub](https://github.com/moodle/moodle)
- [Moodle archived analytics docs](https://web.archive.org/web/20241230102303/https://docs.moodle.org/405/en/Analytics)
- [Moodle archived offline docs](https://web.archive.org/web/2025id_/https://docs.moodle.org/405/en/Moodle_app_offline_features)
- [Instructure](https://www.instructure.com/about)
- [Canvas](https://www.instructure.com/canvas)
- [Canvas tiers](https://www.instructure.com/products/canvas-tiers)
- [Canvas API docs](https://developerdocs.instructure.com/services/canvas)
- [Canvas Outcome Results API](https://developerdocs.instructure.com/services/canvas/resources/outcome_results.md)
- [Canvas offline press release](https://www.instructure.com/press-release/instructure-launches-offline-feature-canvas-student-app-furthering-equitable-access)
- [Canvas Lite press release](https://www.instructure.com/press-release/instructure-announces-canvas-lite-new-free-course-tool-built-educators)
- [Eneza/HundrED](https://hundred.org/en/innovations/shupavu291-an-e-learning-platform-that-can-be-accessed-offline-on-basic-feature-phones-through-sms)
- [Eneza/Engineering for Change](https://engineeringforchange.org/solutions/product/eneza-education)
- [Eneza/African Union](https://education-au.org/139-survey-1/lms-platforms/422-eneza-education-cote-d-ivoire-ghana-kenya)
- [GSMA Eneza material](https://gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/digital-grantees-portfolio/eneza-education)

### Technology and UX

- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [MDN PWA offline guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation)
- [web.dev offline UX](https://web.dev/articles/offline-ux-design-guidelines)
- [web.dev Save-Data](https://web.dev/articles/optimizing-content-efficiency-save-data)
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [W3C WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [KICTANet accessibility guidance](https://kictanet.or.ke/accessibility-101-guidelines-for-organisational-compliance)
- [NN/g dashboards](https://www.nngroup.com/articles/dashboards-preattentive/)
- [NN/g cognitive load](https://www.nngroup.com/articles/minimize-cognitive-load/)
- [NN/g progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [Material Design navigation](https://m3.material.io/components/navigation-bar)
- [Apple HIG tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars.md)
- [Africa's Talking](https://africastalking.com/)
- [AWS](https://aws.amazon.com/)
- [Getting Smart mastery data](https://www.gettingsmart.com/2019/10/16/using-mastery-data-to-measure-growth-in-student-learning/)
- [Edutopia visual rubrics](https://edutopia.org/article/representing-proficiency-progress-visual-rubrics)
- [Smithsonian kanga article](https://festival.si.edu/blog/2014/a-cloth-of-many-meanings-the-khangas-role-in-kenyan-culture)
- [Google Fonts](https://fonts.google.com/)
