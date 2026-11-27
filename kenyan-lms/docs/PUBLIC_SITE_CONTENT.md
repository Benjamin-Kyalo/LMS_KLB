# Public site content

Public wording and appearance are data, not source edits. A single editable
document stores the header and footer, homepage sections, managed photo
addresses, role cards, library book and resource headings, sign in and
registration copy, signed-in brand and portal menu labels, user-facing messages
and safe per-section style controls. The shipped wording is the **KLB Elimu
content pack**, a proposed digital learning initiative subject to organisational
approval; it does not claim official curriculum status.

The pack documents every managed section: `introduction`, `capabilities`,
`libraryFeature`, `audiences`, `steps`, `closingCta`, all entries under
`publicPages`, and `messages`. The homepage also carries a dismissal-friendly
announcement, an on-page quick-link strip, a hero, a short trust strip, three
workspace cards, an everyday routines guide, a plain-language access table, a
preparation checklist beside the three-step guide, a progress panel, an
accessibility commitment, a library spotlight, the role selector, a support
callout, a question list and a back-to-top control. The former quick-facts strip
was removed.

## Managed content sections

These keys are part of the editable document. Administrators change wording and
links through the Words tab; source edits are not needed.

| Section | What it controls |
|---|---|
| `header` | Brand mark, name and subtitle, public menu links, sign-in and school-registration actions |
| `footer` | Introduction, four link groups, photo credit, closing line and disclaimer |
| `hero` | Overline, eyebrow, headline, description, two actions, supporting statement, highlights and managed photograph |
| `announcement`, `quickLinks` | Dismissible notice and the on-page link ribbon |
| `introduction` | Connected-learning explanation under the hero |
| `capabilities` | Four cards for schools, teachers, learners and parents, each with an action link |
| `libraryFeature` | Homepage introduction to the KLB Digital Library, with primary and secondary actions |
| `audiences` | `teachers`, `learners` and `parents` sections with paragraphs and audience actions |
| `steps` | Five getting-started steps under “How it works” |
| `closingCta` | Final invitation, school-registration action and sign-in action |
| `trust`, `workspaces`, `routines`, `access`, `journey`, `insights`, `accessibility`, `spotlight`, `roles`, `support`, `faq` | Remaining homepage panels, guides, role preview and question list |
| `publicPages` | Wording and lists for the managed public routes listed below |
| `messages` | Page introductions, search placeholders, global actions, loading, success, errors, confirmations, empty states, first-time notes and notifications |
| `library`, `auth`, `portal`, `app` | Library fields, sign-in/registration/invitation stories, portal tutor wording, signed-in brand and portal menu labels |
| `styles` | Section-scoped appearance controls described below |

The managed `publicPages` keys map to these public routes:

| Key | Route | Page |
|---|---|---|
| `about` | `/about` | About KLB Elimu and its proposed brand message |
| `schools` | `/for-schools` | School audience page |
| `teachers` | `/for-teachers` | Teacher audience page |
| `learners` | `/for-learners` | Learner audience page |
| `parents` | `/for-parents` | Parent audience page |
| `library` | `/library` | Public book and resource catalogue introduction |
| `contact` | `/contact` | Contact form, categories, confirmation and enquiry fields |
| `help` | `/help` | Searchable help topics and support callout |
| `faq` | `/faq` | Expandable common questions |
| `privacy` | `/privacy` | Privacy Notice |
| `terms` | `/terms` | public Terms of Use |
| `acceptableUse` | `/acceptable-use` | Acceptable Use Policy |
| `accessibility` | `/accessibility-statement` | Accessibility Statement |

`/academic-terms` remains the legacy school-term editor in the admin side; it
is not the public Terms of Use. The public `/terms` route renders the managed
Terms of Use. Policy pages may carry a legal-review note; implementer-only notes
are never rendered on a public page. No outcome is promised for an enquiry,
including a response time.

## Admin editor

Administrators open **Administration → Appearance** (`/admin/appearance`). The
page has four tabs so appearance work has one destination:

| Tab | Who can edit | What it changes |
|---|---|---|
| Colours | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Active palette and custom palettes |
| Photos | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Managed public and portal photographs |
| Words | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Header, footer, homepage, library and auth wording |
| Styles | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Section-scoped colours, corners and spacing |

A custom role only reaches these tabs when `admin.access` is picked; the backend
enforces `appearance.manage` and the section-style safety rules.

The older `/admin/theme` and `/admin/site-content` addresses still work; they
open the Appearance page with the Colours or Words tab selected. The Words tab
groups fields into simple sections. Text is edited in text boxes, lists use one
line per row, and repeatable cards have an **Add an item** button. The Styles tab
has one section at a time so a change cannot leak into another panel. Saving
calls:

```text
PATCH /api/theming/site-content/
```

The live saved response is read by the frontend and shown on public pages and
the learner portal. `SUPER_ADMIN` and `ADMIN` can manage the shared photographs,
wording and section styles; a custom role needs `admin.access` plus
`appearance.manage`.

This is a normal web app: there is no service worker, PWA shell or native app.
By default a failed save shows an error and the old values stay on the server.
The separately documented low-bandwidth reversal is off by default; when
enabled, it may cache allowlisted public reads and queue allowlisted theming
writes, never credentials, CSRF tokens or personal fields. See
`OFFLINE_MODE_REVERSAL.md`.

Every save writes a `site_content.updated` audit entry. Links are limited to
site paths such as `/library` or full HTTPS addresses. Script, data and
protocol-relative links are rejected, and unknown fields are discarded.

## Managed photos

The **Photos** tab of `/admin/appearance` manages every photograph used by the
public site and learner portal. Each slot has a preview, a file picker and
three actions: upload or replace, restore the shipped default, and remove.
Uploads publish immediately; a failed action shows an error and leaves the
previous photo in place. `SUPER_ADMIN` and `ADMIN` can upload a JPG, PNG or WebP
file; a custom role needs `admin.access` plus `appearance.manage`. These photographs are shared across the whole
site, so a change made by one administrator is visible everywhere. Uploads must
be at least 640×360 px and at most 5 MB. Each Photo card checks the type, size
and decoded dimensions in the browser before enabling **Upload photo** or
**Replace photo**; an unsuitable file shows the exact reason inline and is not
sent. The backend independently checks the file name, bytes and decoded image,
stores the file under `MEDIA_ROOT/site-content/<slot>/`, updates only the
selected content field and writes an audit entry. If a server-side check still
rejects a file, the notification shows that validation message instead of a
generic `Bad Request`. Free-text image paths were removed from the wording
editor, so a wording save cannot silently replace a photograph.

| Photo slot | Field | Where it appears |
|---|---|---|
| Homepage hero | `hero.imageSrc` | Public homepage hero |
| Learning workspace | `workspaces.cards[0].image` | First homepage workspace card |
| School day | `workspaces.cards[1].image` | Second homepage workspace card |
| Digital publishing | `workspaces.cards[2].image` | Third homepage workspace card |
| Progress insight | `insights.imageSrc` | Homepage progress panel |
| Library spotlight | `spotlight.imageSrc` | Homepage library spotlight |
| Sign-in story | `auth.login.storyImageSrc` | Sign-in story panel |
| Registration story | `auth.register.storyImageSrc` | Registration and invitation pages |
| Portal tutor | `portal.tutorImageSrc` | Learner and guardian tutor workspace |

The supplied photos are the defaults for the homepage hero, first and second
workspace cards, progress panel, sign-in story, registration story and portal
tutor. The third workspace card and the library spotlight use locally hosted
catalogue and stock images until an administrator uploads replacements.

A production deployment must serve `MEDIA_URL` from the same origin or through a
configured CDN; Django only serves uploaded media automatically in debug mode.

## Section styles

The **Styles** tab changes one public section at a time. Each section has four
colour controls (background, text, accent and border), a corner style and a
spacing choice. An empty colour or **Inherit** means the shipped design or the
active palette stays in charge. The saved values are applied as CSS custom
properties on that one section element, so changing the portal tutor card does
not change the homepage hero or the global palette. No raw CSS is accepted.

Only these allowlisted IDs can carry section styles:

| ID | Section | Where it applies |
|---|---|---|
| `header` | Public header | Brand, menu and sign in bar |
| `footer` | Public footer | Closing strip on public pages |
| `hero` | Homepage hero | First panel and its buttons |
| `introduction` | Homepage introduction | Connected-learning explanation beneath the hero |
| `capabilities` | What you can do | Four school, teacher, learner and parent cards |
| `library-feature` | Digital library feature | Section introducing the KLB Digital Library |
| `teachers` | Teacher audience | Teacher section on the homepage |
| `learners` | Learner audience | Learner section on the homepage |
| `parents` | Parent audience | Parent section on the homepage |
| `how-it-works` | Getting started steps | Five-step setup guide on the homepage |
| `closing-cta` | Closing invitation | Final invitation before the questions |
| `announcement` | Homepage announcement | Short notice and action under the header |
| `quick-links` | Quick links | On-page link ribbon under the announcement |
| `trust` | Homepage trust strip | Three short value points under the hero |
| `workspaces` | Workspace introduction | Heading above the workspace cards |
| `routines` | Daily routines | Three everyday routine cards |
| `access` | Access guide | Who-sees-what table |
| `workspace-learning` | Learning workspace | First workspace card only |
| `workspace-school` | School day | Second workspace card only |
| `workspace-publishing` | Digital publishing | Third workspace card only |
| `journey` | Getting started | Three-step guide and readiness checklist |
| `insights` | Progress insight | Homepage progress points and photo |
| `accessibility` | Usability commitment | Keyboard, motion and connection notes |
| `info` | Public information pages | About, role, help, contact and policy pages |
| `spotlight` | Library spotlight | Library invitation and photo on the homepage |
| `roles` | Where do you fit? | Role selector and preview |
| `support` | Support callout | Help invitation before the questions |
| `faq` | Common questions | Expandable question list near the end of the homepage |
| `library` | Library | Public book and resource library |
| `login` | Sign-in story | Story panel beside the sign in form |
| `register` | Registration story | Registration story panel |
| `invite` | Invitation story | Administrator invitation story panel |
| `tutor` | Portal tutor | Tutor introduction in the learner portal |

Colours must be six-digit hex values. Corner choices are `0px`, `8px`, `16px`
and `24px`; spacing choices are `compact`, `comfortable` and `relaxed`. If both
background and text are set, they must reach 4.5:1 contrast. Semantic status
colours for errors, success, warnings and information are never changed by
section styles. Focus rings, accessible names and reduced-motion behaviour
remain untouched.

## Role previews

The public role selector has three previews: learners, guardians and teachers.
The old Content managers preview is retired. It is removed from the frontend
defaults, the backend defaults, saved site data and PATCH payloads, so stale
data cannot bring it back.

## Homepage navigation and footer

The public header is shared by the homepage, library, sign-in, registration and
invitation pages. It is sticky on desktop and collapses into a labelled **Menu**
button on narrow screens. The button keeps a visible label, reports its state
with `aria-expanded`, closes on link selection or Escape, and never hides the
sign-in link from keyboard or screen-reader users. Signed-in visitors keep the
same session and see a workspace link instead of a second sign-in action.

The footer has a name, tagline and contact lines, then four link groups:
**Explore** (`exploreLinks`, titled “Platform”), **Resources** (`learnLinks`),
**Information** (`infoLinks`) and **Contact** (`supportLinks`). It also manages a
photo credit, a `closingLine` (“Every lesson opens a door.”) and a `disclaimer`
describing the initiative as proposed and subject to organisational approval.
A labelled **Back to top** button returns to the homepage start and honours a
reduced-motion preference. It uses the same safe-link check as the header. Link
columns stay on site paths or full HTTPS addresses; they do not expose
administration links or repeat the sign-in and registration actions. If a
deployment clears the photo credit wording, the empty credit link is not
rendered.

A keyboard user can reach the main content directly with the **Skip to homepage
content** link. A thin reading-position indicator sits above the sticky header.
Both are presentational helpers: neither traps focus nor changes the site
session. The announcement ribbon can be dismissed for the current page view and
its action uses the managed safe-link rule. Quick links, the support callout and
the readiness checklist are ordinary editable text, not extra navigation
permissions.

## Library wording and artwork

The Library group edits both parts of `/library`. The page introduction uses
`library.overline`, `library.title` and `library.description`. The book shelf uses
the `booksOverline`, `booksTitle` and `booksDescription` fields. The resource
catalogue uses the `resourcesOverline`, `resourcesTitle` and
`resourcesDescription` fields. Changing any of these fields updates the public
page after saving, with no source edit or rebuild.

The book shelf only shows published, non-expired catalogue metadata from
`/api/content/public/books/`. It never exposes chapter content or downloads.
Full book access stays with the licensed portal and the institution
administrator (`ADMIN`).
Public book cards display `cover_url`, and public resource cards display
`thumbnail_url`. Both are locally hosted, responsive and accompanied by
meaningful fallback artwork when a file is unavailable. Curators can replace a
resource thumbnail with the **Card thumbnail** field on the resource form.

## API

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/theming/site-content/` | Public | Return the full merged document |
| PATCH | `/api/theming/site-content/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Validate and save edited wording or section styles |
| POST | `/api/theming/site-content/image/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Validate, upload and publish any allowlisted photo slot |
| DELETE | `/api/theming/site-content/image/{slot}/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Clear one managed photo slot |
| POST | `/api/theming/site-content/image/{slot}/reset/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Restore one slot to its shipped default |
| POST | `/api/theming/site-content/hero-image/` | `SUPER_ADMIN`, `ADMIN`, or custom role with `appearance.manage` | Legacy homepage-hero alias; still writes `hero.imageSrc` |

A PATCH may send the whole document or only the sections being changed. Omitted
fields keep their current values. GET always returns the full document so the
frontend can render it directly.

The managed `/contact` page posts to `POST /api/core/public-enquiries/`.
Submission is public and throttled; it returns a real reference number. Only
`SUPER_ADMIN` can read or update the review queue. See
`API_DOCUMENTATION.md`.

## Safety rules

Every managed link is allowlisted: it must be a site path such as `/library` or
a full `https://` address. Script, data and protocol-relative links are
rejected with a field error, and unknown fields are discarded. Raw CSS is not
accepted anywhere: section styles offer only six-digit hex colours plus the
listed corner and spacing choices, and a background/text pair must reach 4.5:1
contrast. Focus rings, accessible names, status colours and reduced-motion
behaviour are not editable. Retired role cards and retired navigation items are
stripped from defaults, saved data and PATCH payloads. See
`OFFLINE_MODE_REVERSAL.md` for the opt-in cache/outbox and what it refuses to
store.

## Defaults, migrations and connection failures

The frontend content-pack defaults live in
`frontend/src/config/publicContentPack.json` and are loaded through
`frontend/src/config/publicSite.js`. The backend defaults in
`backend/apps/theming/site_content.py` mirror that JSON exactly; a parity test
(`test_frontend_default_pack_matches_backend_defaults`) compares the two.

Earlier migrations still matter: `theming.0007_refresh_public_homepage`
installs the redesigned hero, navigation, trust strip, guide, spotlight,
questions and footer fields, and `theming.0008_add_public_homepage_extras` adds
the announcement, quick links, routines, access guide, accessibility notes,
support callout, readiness checklist and "Who sees what" footer link. Both only
replace known old values or fill missing fields.

Migration `theming.0009_apply_klb_elimu_content_pack` applies the KLB Elimu pack
to an existing saved document. It freezes the pack values in the migration file,
replaces only known old brand and path values, fills missing sections and new
fields, and keeps administrator edits such as custom wording, photos and
credits. Before changing anything, it stores the exact pre-migration document at
the SiteContent key `public_before_klb_elimu_content_pack`. The reverse operation
restores that stored snapshot verbatim and removes the backup key, so the
migration can be reversed without losing administrator edits. A round-trip test
covers this behaviour.

The frontend merges, in order:

1. built-in defaults from the content pack
2. an optional `window.__KLB_SITE_CONFIG__` deployment override
3. the live `/api/theming/site-content/` response

If the API is unreachable, the defaults are used and the page reports that the
content could not be loaded. By default there is no local content cache, queue
or replay: a failed PATCH leaves the server copy unchanged and shows an error to
the administrator. If low-bandwidth mode is explicitly enabled, only the
allowlisted public reads and theming writes in `OFFLINE_MODE_REVERSAL.md` may use
device storage.

## Optional runtime override

A deployment can add a small override before React mounts. This remains useful
for temporary deployment wording, but ordinary edits should use the admin page.

```html
<script>
  window.__KLB_SITE_CONFIG__ = {
    content: {
      footer: { name: "Custom KLB site" },
      roles: { title: "Find your place here" },
    },
  };
</script>
```

Legacy `footer`, `libraryCta` and `rolePreviews` keys are still accepted and
mapped into the same document. Tests cover the defaults, a runtime override and
the administrator save workflow.

## Wording style

Copy is written in plain, friendly English. Avoid unnecessary dashes and long
labels. When adding a role card, keep its `key` unchanged because the key maps to
the icon and workspace link. Describe only access the backend actually grants.
