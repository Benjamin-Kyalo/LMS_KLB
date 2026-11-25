# Reference models and design guidance

## 1. What this document is for

The strategy report
`C:\Users\Admin IT\Downloads\LMS\LMS\Kenyan_Digital_Learning_Ecosystem_Strategy_Report.md`
studies five systems. This page confirms the five reference models and records
which **idea** this project borrowed from each one. It is a design reference,
not a claim that this product is affiliated with, endorsed by, or derived from
those systems.

## 2. The five confirmed reference models

| # | Reference model | Idea borrowed for this LMS | What is not copied or is not built |
|---|---|---|---|
| 1 | **Zeraki** (Kenya) | The school-operations loop: reliable admission numbers, attendance and marks feeding a dashboard, and a parent-facing view of progress. The staff dashboard and linked learner report follow this idea. Its public-site information hierarchy also inspired the bold hero, three workspace cards, visible progress area and role cards on the KLB homepage. The facts strip was later removed at the user's request. Repeated quick-access links were deliberately omitted; the role section now uses a selector that shows one role's rights, content and workspace link at a time. | Fees, school finance, SMS, biometric touch and LAN/TV deployment are not implemented. The strategy report also warns that marks-centric reporting does not show CBE competency evidence. No Zeraki branding, copy, images, layout assets or code were copied; the KLB palette, wording and routes remain original. |
| 2 | **ShuleSoft** (Tanzania) | One canonical learner identity across SIS, LMS and content, and a plain-language parent view with one clear action. The portal home and school messages follow this idea. | ERP breadth, payment ledger, WhatsApp/SMS delivery and guided migration tooling are not implemented. |
| 3 | **Moodle** | Course modules, reusable question banks, competency frameworks, completion-style progression and explicit offline constraints. The modules, questions and curriculum follow these ideas. *(The earlier PWA work inspired by this reference was removed; see section 6.)* | No Moodle source code, plugin system, theme or branding is used. This is a Django/React implementation, web-only. |
| 4 | **Canvas** | Modules as the course spine, rubric/outcome-to-mastery thinking, clear feedback in grading, and criterion-based messaging. The module pages, assignments, exams and reports follow these ideas. | No SpeedGrader branding, blueprint courses, LTI marketplace or Canvas code is used. |
| 5 | **Eneza Education / Shupavu291** (Kenya) | Text-first, low-friction access and immediate explanatory feedback, adapted here as a lightweight, responsive **web app**. *(An earlier offline-friendly PWA with cached reads and queued writes was built and then removed; that part is historical.)* | USSD/SMS revision and Ask-A-Teacher are not built. The strategy report notes that independent research did **not** verify better learning outcomes from Shupavu291, so it is treated as an access pattern only. |

The "idea borrowed" column corresponds to the "Five valuable concepts to
borrow" tables in sections 4–8 of the strategy report. Where the report says
*Adapt* or *Borrow selectively*, this prototype implements only the part that
fits the current **normal web app** scope. Offline/PWA adaptations in earlier
milestones are historical and no longer implemented.

## 3. Original design — no copied branding or code

- The names above are used only as **references** in research and planning.
- No logos, screenshots, product artwork, marketing text or distinct layout
  from those systems were copied into this project.
- No source code from those systems was copied. Moodle core is GPL-3.0 and
  Canvas core is AGPLv3; this project does not include either codebase. It uses
  its own Django/DRF and React code with its own dependencies.
- No claim of partnership or endorsement is made.
- The colour palette, typography and component style are defined locally in
  `frontend/src/styles/tokens.css` and documented in `docs/DESIGN_SYSTEM.md`.

## 4. Accessibility guidance: WCAG 2.2 AA

The strategy report sets **WCAG 2.2 AA** as the engineering baseline. Keep
these points in mind when adding pages or charts:

- Text contrast of at least 4.5:1 against its background; decorative blue steps
  (`--ocean-600` and lighter) are never used for small text (use `--link` or
  `--ink` instead).
- Keyboard access, visible focus, sensible tab order and no keyboard traps.
- Labels for inputs and charts, alternatives for meaningful images, captions
  for media.
- Reflow at 320 px without loss of content; target sizes large enough for
  touch.
- Plain language, predictable navigation and status messages that can be
  announced by assistive technology.

The palette has calculated contrast ratios, and chart cards use
`ResponsiveContainer` with an empty-state message. This is **guidance, not a
completed audit**: no formal WCAG 2.2 AA audit with assistive technology has
been performed. Record that limitation in release notes.

## 5. Kanga-inspired visual restraint

The strategy report recommends using kanga *structure*, not kanga wallpaper:

- a thin, semantic border on achievement or subject surfaces;
- one restrained central motif per subject or level, not busy decoration;
- a short, plain-language "message" label, like the kanga `jina`, where a
  learner or parent needs guidance.

In this codebase that means thin pale-blue borders, the primary-blue rule under
page headings, calm chart colours and short hints such as "Open learner
records" on dashboard cards. Do not add patterned backgrounds that compete
with data. See `docs/DESIGN_SYSTEM.md` for the tokens.

## 6. Low-bandwidth web guidance (PWA guidance superseded)

Kenyan learners may share devices and connections, so keep pages cheap to
load. Earlier PWA guidance (service-worker app-shell cache, NetworkFirst API
cache, IndexedDB mutation queue and conflict replay) is **superseded**; none of
it exists in the current app.

- `npm run build` produces only `index.html`, hashed CSS/JS assets,
  `robots.txt`, SVG marks and local images. There is no app-shell or API cache.
- Failed mutations surface an error and remain unsaved; there is no local queue
  or automatic replay on reconnection. Uploads require a live connection.
- School logos are limited to JPG, PNG or WebP and at most 2 MB, with
  magic-byte sniffing on the server.
- Charts should collapse gracefully on small screens via CSS grid and
  `ResponsiveContainer`; never ship a large decorative image where a bordered
  card will do. The homepage particle headline preserves a real `<h1>` and
  respects reduced motion.
- Test on a throttled connection where possible before shipping new content.

Implementation details are in `docs/SYSTEM_OVERVIEW.md`. Current verification
status is in `docs/TESTING_CHECKLIST.md`.
