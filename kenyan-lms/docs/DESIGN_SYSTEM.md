# Design system

The palette is defined in one file:
`frontend/src/styles/tokens.css`. Change it there, never in individual
components.

## Colour hierarchy

| Role | Token | Hex | Use | Contrast on white |
|---|---|---|---|---|
| Primary | `--forest` | `#0B3D2E` | Buttons, active navigation, headings | 12.2:1 (AAA) |
| Primary dark | `--forest-2` | `#14563F` | Hover states | 8.6:1 (AAA) |
| Secondary | `--blue` | `#1C5D7E` | Links, info notices, focus rings, charts | 7.2:1 (AAA) |
| Secondary dark | `--blue-2` | `#165E83` | Blue hover states | 7.1:1 (AAA) |
| Background | `--paper` | `#F7F4ED` | Page background | — |
| Surface | `--surface` / `--white` | `#FFFDF8` / `#FFFFFF` | Cards, tables, modals | — |
| Green tint | `--green-tint` | `#E3EFE9` | Selected rows, success notices | — |
| Blue tint | `--blue-tint` | `#E8F0F6` | Info notices | — |
| Accent (decorative) | `--ochre` | `#C98A2B` | Rules, dots, badges | 2.9:1 — **not for text** |
| Accent (readable) | `--amber-text` | `#8A5A15` | Warning text, readable accents | 5.9:1 (AA) |
| Error | `--bad` | `#A13B2E` | Errors only | 6.6:1 (AA) |
| Success | `--good` | `#2E6B4F` | Success states | 6.3:1 (AA) |
| Muted text | `--ink-faint` | `#5F6B65` | Overlines, captions, secondary labels | 5.6:1 on white, 4.6:1 on `--paper-2` (AA) |

Ratios were calculated with the WCAG relative-luminance formula, not
estimated. Green is deliberately dominant: blue-led interfaces are the
generic SaaS default this project set out to avoid. Blue supports green;
white is a surface, not the whole page.

## Type and shape

- Display: Iowan Old Style / Palatino / Georgia — editorial, textbook feel.
- Body: Segoe UI / system UI.
- Mono: Cascadia Code / Consolas — numbers, codes, admission numbers.
- Radius: 6px. Borders are thin and low-contrast; the green rule under
  page headings is the main structural device.

## Component conventions

- `.notice.info` uses blue; `.notice.success` uses green tint;
  `.notice.warn` uses amber; `.notice.error` uses clay red.
- `.tag.info` is blue; `.tag.good`, `.tag.warn`, `.tag.bad` follow semantics.
- `.stat.secondary` gives a blue alternative to the default green stat.
- `button.info` is the blue secondary action; the default button stays green.
- Public pages use a hero → photographed workspace cards → facts strip →
  progress/insights → interactive role selector rhythm. Selecting a role reveals
  that role's rights and content; only the selected role's workspace link is
  shown. Links are intentionally sparse: one generic registration path, one
  generic sign-in path and section anchors only in the topbar. Footer text comes
  from `frontend/src/config/publicSite.js`, not the component. Admin and portal
  pages reuse the same strong section heads, coloured top rules on cards, clear
  active-navigation fills and compact data tables. This is an
  information-hierarchy pattern only; the required KLB palette and copy are
  retained. Locally hosted Unsplash photographs and the original KLB SVG are
  credited in `docs/ASSET_CREDITS.md`; no external branding is used.

## Accessibility rule

Never use `--ochre` for text. If an amber word must be read, use
`--amber-text`. Every text/background pair used in the UI must reach at
least 4.5:1; prefer AAA where practical.
