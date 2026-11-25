# Ocean Blue Serenity palette

Approved by the user on 24 November 2026. Source image:
`C:\Users\Admin IT\Downloads\Ocean Blue Serenity.png`.

**Current status (25 November 2026):** Plum Harvest is now the active palette
and the fresh-install default, and status messages use fixed red/green/amber/blue
colours. The blue-only semantic decision recorded below is the historical
decision for this palette, not the present UI state.

## Exact extracted values

The image was sampled programmatically. Its nine blue swatches are:

| Step | Hex | WCAG ratio on white | Permitted use |
|---|---|---:|---|
| Ocean 100 | `#CAF0F8` | 1.21:1 | Pale tint: hovers, selected rows, notices, illustration fills |
| Ocean 200 | `#ADE8F4` | 1.34:1 | Slightly stronger tint: warning backgrounds, muted text on dark blue |
| Ocean 300 | `#90E0EF` | 1.49:1 | Borders, decorative fills, muted text on dark blue |
| Ocean 400 | `#48CAE4` | 1.94:1 | Decorative rules, borders, badges; not small text |
| Ocean 500 | `#00B4D8` | 2.46:1 | Charts and decorative accents only |
| Ocean 600 | `#0096C7` | 3.39:1 | Icons, large UI, chart series; not small body text |
| Ocean 700 | `#0077B6` | 4.87:1 | Links, info text, focus rings, muted text on white (AA) |
| Ocean 800 | `#023E8A` | 10.20:1 | Primary actions, active navigation, body text (AAA) |
| Ocean 900 | `#03045E` | 17.75:1 | Headings, darkest panels, semantic error emphasis (AAA) |
| White | `#FFFFFF` | — | Page, card, table, form and modal backgrounds |

The image also contained black `#000000`, grey `#7D7C83` and a tiny
`#0066FF` artefact. These are not brand colours and are not used by the UI.

## Decision: strict blue-only semantics

The earlier suggestion to retain small red/amber warning colours was rejected in
favour of the approved palette. Errors, warnings, success and information are
now all expressed inside the blue ramp. Meaning is carried by:

- the literal message text (`error`, `warning`, `success`, `info` wording from
  the existing components);
- border weight: errors use a 6px left border, other notices 4px;
- border style: warnings use a dashed border;
- background step: info `#CAF0F8`, warning/success/error `#ADE8F4`;
- text colour: `#03045E` on pale backgrounds, which is at least 13.21:1.

No red, amber, green, ochre or clay value remained in `frontend/` at that point.

The exact Ocean Blue values remain the historical record for this palette, but
the blue-only semantic decision was later superseded by fixed semantic status
colours. **Superseded:** the historical implementation/verification notes mention
PWA metadata and a service-worker precache; those files and the PWA were later
removed. The build now emits only `index.html`, hashed CSS/JS, `robots.txt`,
SVG marks and local images. See `README.md`.

## Implementation points

- Tokens and usage rules: `frontend/src/styles/tokens.css`
- Shared CSS: `frontend/src/styles/global.css`
- JS/SVG/chart constants: `frontend/src/styles/palette.js`
- Charts: `frontend/src/components/ChartCard.jsx`, `Dashboard.jsx`,
  `PortalHome.jsx`, `Reports.jsx`
- Web app metadata (former PWA metadata): `frontend/index.html`; there is no
  `manifest.webmanifest` now
- Original artwork: `frontend/public/mark.svg`, `frontend/public/hero-learning.svg`
- Accessible canvas hero: `frontend/src/components/ParticleHeadline.jsx`
  (real `<h1>`, reduced motion, pointer/touch repulsion, resize and cleanup)

## Verification after the change (historical; superseded counts)

These were the results at the time of the palette change; they are not the
current regression figures.

- Frontend unit tests: **52 passed across 19 files**
- Production build: successful, **7** PWA precache entries (PWA later removed)
- `npm audit --audit-level=moderate`: **0 vulnerabilities**
- In-app browser, public `/`: body/card background `rgb(255,255,255)`;
  hero/footer `rgb(2,62,138)`; **0** horizontal overflow; **0** `/admin` links;
  no console errors
- In-app browser, `/login`, `/register` and `/portal → /login`: white
  backgrounds, **0** horizontal overflow, **0** `/admin` links, no console errors
- Lighthouse on the public homepage after the palette change: accessibility
  **1.00**, Best Practices **1.00**, SEO **1.00**

A physical-device viewport replay and a human visual design review were still
outstanding at the time. The palette change alters colours only, not layout
structure. Current browser checks cover responsive layout and the canvas
hero's reduced-motion fallback under forced media; assistive-technology review
and production readiness are still not claimed (see `SECURITY_AUDIT.md`).
