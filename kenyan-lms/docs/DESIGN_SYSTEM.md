# Design system

**Current direction:** normal web app only. The PWA/offline UI (sync banners,
queued-change notices and the dedicated sync page) was removed. The visual
system below describes the current palette and interaction conventions; earlier
palette states are recorded historically. The homepage hero uses an accessible
canvas particle headline with a real `<h1>` and reduced-motion support. See
`README.md` and `SECURITY_AUDIT.md`.

## Runtime palette model

The palette is no longer a set of literals duplicated across CSS and JavaScript.
The Django `apps.theming` catalogue owns the palettes and the single active
selection. The frontend fetches `/api/theming/active/` through `ThemeProvider` and
injects `--ramp-900` … `--ramp-100` CSS custom properties onto `:root`. There is
no offline cache; a failed theme fetch falls back to the local ramp. Brand and
action tokens in `frontend/src/styles/tokens.css` alias those ramp variables, so
a palette change reaches the public site, staff admin, learner/guardian portal,
charts and browser theme colour without component edits. Status colours are
fixed so error, success, warning and info keep their familiar meanings.

- `backend/apps/theming/` — palette model, validation, public active read and
  admin CRUD/activation endpoints.
- `frontend/src/context/ThemeContext.jsx` — fetches, caches and applies the
  active palette.
- `frontend/src/styles/tokens.css` — semantic aliases plus the Plum Harvest
  fallback ramp used before the API responds or when the request fails.
- `frontend/src/styles/palette.js` — helpers that derive CSS variables, chart
  series colours and WCAG contrast values from the active palette.

The original extraction and approval record for Ocean Blue Serenity is
`docs/OCEAN_PALETTE.md`; its earlier active state is historical. **Current
status (25 November 2026):** the catalogue has **eight** built-in palettes —
Ocean Blue Serenity, Sage Green, Blue Coral Daylight, Forest Green, Citrus
Bloom, Heritage Spice, Bright Horizon and Plum Harvest. Plum Harvest
(`plum-harvest`) is both the active selection and the fresh-install default after
the local `theming.0004_seed_and_activate_plum_harvest` migration. Administrators
can apply any of them from **Administration → Theme & colours** at `/admin/theme`.
`SUPER_ADMIN` and `ADMIN` can also manage the catalogue; a custom role needs
`admin.access` plus `appearance.manage` (backend-enforced). Learners, guardians
and teachers cannot.

The six palettes added after the original Ocean Blue Serenity and Sage Green
pair are:

| Palette | Source image | Exact swatches kept in the ramp |
|---|---|---|
| Blue Coral Daylight | `new color.png` | `#324376`, `#586BA4`, `#F76C5E`, `#F68E5F`, `#F5DD90` |
| Forest Green | `color 2.png` | `#03440C`, `#036016`, `#04773B`, `#058E3F`, `#069E2D` |
| Citrus Bloom | `color 3.png` | `#FF37A6`, `#43B929`, `#87E752`, `#5CF64A`, `#FFCAE9` |
| Heritage Spice | `color 4.png` | `#034732`, `#008148`, `#EF2917`, `#EF8A17`, `#C6C013` |
| Bright Horizon | `color 5.png` | `#FF5964`, `#35A7FF`, `#6BF178`, `#FFE74C` |
| Plum Harvest | `color 7.png` | `#291720`, `#820263`, `#D90368`, `#04A777`, `#FB8B24` |

Plum Harvest's full ramp is 900 `#1A0F14`, 800 `#291720`, 700 `#820263`,
600 `#D90368`, 500 `#04A777`, 400 `#FB8B24`, 300 `#FFB067`, 200 `#FFD9B8`
and 100 `#FFF3E8`. Darker 900/800/700 steps are derived where needed so text
shades pass the 4.5:1 admin contrast check; lighter steps are derived from the
lightest source swatch. The earlier seeding migrations are idempotent and leave
the active selection alone; `theming.0004_seed_and_activate_plum_harvest` was
applied locally to seed and activate Plum Harvest.

## Fallback palette hierarchy (Plum Harvest)

These are the fallback values for Plum Harvest. When another palette is active,
the same token roles follow that palette's ramp.

| Step | Token | Default hex | Use |
|---|---|---|---|
| 900 | `--ramp-900` / `--ink` | `#1A0F14` | Headings, dark panels, text on pale surfaces |
| 800 | `--ramp-800` / `--primary` | `#291720` | Buttons, active navigation, rules, body text |
| 700 | `--ramp-700` / `--link` | `#820263` | Links, focus rings, muted text on white |
| 600 | `--ramp-600` | `#D90368` | Charts and decorative accents; not small text |
| 500 | `--ramp-500` | `#04A777` | Charts and decorative accents; not text |
| 400 | `--ramp-400` | `#FB8B24` | Borders, badges, decorative rules |
| 300 | `--ramp-300` | `#FFB067` | Borders, illustration fills |
| 200 | `--ramp-200` / `--tint-strong` | `#FFD9B8` | Strong pale tint |
| 100 | `--ramp-100` / `--tint` | `#FFF3E8` | Hover and selected rows |
| Page/surface | `--paper` / `--surface` / `--white` | `#FFFFFF` | Page, cards, tables, forms, modals |

Text on pale tints uses `--ink`; the administrator form checks that the three
darkest shades of every palette reach at least 4.5:1 on white.

## Semantic states

Status colours are fixed and independent of the active palette, so changing the
brand ramp never changes what a message means: red error (`--bad`), green success
(`--good`), amber warning (`--warn`) and blue info (`--info`). The ramp supplies
brand, action, focus and chart colours.

| State | Border | Background | Text | Extra cue |
|---|---|---|---|---|
| Info | `--info` solid | `--info-bg` | `--info-ink` | Message wording |
| Success | `--good` solid | `--success-bg` | `--good-ink` | Message wording |
| Warning | `--warn` dashed | `--warn-bg` | `--warn-ink` | Message wording |
| Error | `--bad` solid with a heavier left edge | `--error-bg` | `--bad-ink` | Message wording |

Never rely on colour alone. The existing components already render words such
as “Error” and “Warning”; preserve them. The former “Queued offline” notice,
`SyncStatus` banner and dedicated sync page were removed with the offline
queue. A failed mutation now shows an ordinary error and the change remains
unsaved.

## Particle headlines

`frontend/src/components/ParticleHeadline.jsx` draws the homepage, sign-in and
registration headlines on a canvas. Each heading uses a restrained palette
gradient with a soft halo and a short left-to-right settle, so the assembly
reads as deliberate typography rather than random noise. Dark headings use
white through warm ivory into bright cyan; the light-background registration
heading moves from deep navy through royal blue into cyan. The accessible
`<h1>` stays legible beneath the particles at a palette-aware base opacity, so
hover repulsion can never make the words disappear; the motion is a gentle
shimmer that reconstructs quickly on pointer leave. Accessibility is part of
the component, not an afterthought: the real text stays in the DOM, the canvas
is decorative and `aria-hidden`, `prefers-reduced-motion` disables the
animation, pointer and touch repulsion work on their respective devices, and
the canvas resizes responsively and cleans up its listeners/animation frame on
unmount. Keep the real heading when editing copy.

## Type and shape

- Display: Century Gothic / Tw Cen MT / Avenir Next / Segoe UI.
- Body: Century Gothic / Tw Cen MT / Avenir Next / Segoe UI / system UI.
- Mono: Cascadia Code / Consolas — numbers, codes, admission numbers.
- Radius: 6px. Borders are thin palette tints; the primary rule under page
  headings is the main structural device.
- Century Gothic is the preferred face. The fallbacks keep a calm geometric
  feel where the font is not installed. The values live in
  `frontend/src/styles/tokens.css`.

## Component conventions

- `.notice.info`, `.notice.success`, `.notice.warn` and `.notice.error` use the
  fixed `--info`, `--good`, `--warn` and `--bad` tokens with their matching tinted
  backgrounds; errors also have a heavier left edge.
- `.tag.info`, `.tag.good`, `.tag.warn` and `.tag.bad` use the same fixed status
  colours, independent of the active palette.
- `.stat.secondary` gives a lighter alternative to the default primary stat.
- `button.info` and links use `--link`; the default button stays `--primary`.
- Recharts series come from `useTheme().colors.chart` and attendance/score
  colours from the same derived theme object. No chart hardcodes a hex value.
- Public pages use a hero → photographed workspace cards → progress/insights →
  interactive role selector rhythm. The former facts strip was removed. Selecting a role reveals
  that role's rights and content; only the selected role's workspace link is
  shown. Links are intentionally sparse: one generic registration path, one
  generic sign-in path and section anchors only in the topbar. Header, footer and
  section wording come from the managed site content document, with local
  defaults in `frontend/src/config/publicSite.js`. Administrators edit it at
  `/admin/appearance` (Words tab; `/admin/site-content` remains an alias);
  components do not hardcode public copy. Admin and portal
  pages reuse the same strong section heads, coloured top rules on cards, clear
  active-navigation fills and compact data tables. This is an
  information-hierarchy pattern only; the KLB palette and copy are retained.
  Locally hosted photographs and the original KLB SVG are credited in
  `docs/ASSET_CREDITS.md`; no external branding is used. The homepage and sign-in
  story share one administrator-managed photograph.
- Clicks, cards and route changes use short easing transitions. They stay under
  200ms, avoid layout shifts and are disabled under `prefers-reduced-motion`.

### Button interactions

The UI uses a small local interaction layer: `RollingLabel` keeps a real,
always-present accessible label and adds a decorative duplicate for rolling
hover/focus text; `AnimatedSubmitButton` gives authentication submits brief press
feedback; and `HoldToConfirmButton` gives destructive actions a measured hold
fill with an immediate Enter/Space fallback. Busy controls show visible rotating
labels and set `aria-busy`. Focus rings, reduced-motion behaviour, dialog
semantics, accessible names and the fixed semantic status colours above are
preserved. This motion is custom CSS/React inspired by `motion.dev/ui/buttons`:
no new dependency and no generic AI-looking form template was introduced.

## Accessibility rule

Every text/background pair used in the UI must reach at least 4.5:1; prefer AAA
where practical. Ramp steps 600, 500, 400 and 300 are decorative only and must
never be used for small text. The palette manager enforces the dark-shade rule
and shows live contrast feedback. Lighthouse scored the public homepage **1.00**
for accessibility, Best Practices and SEO after the palette system was applied.
