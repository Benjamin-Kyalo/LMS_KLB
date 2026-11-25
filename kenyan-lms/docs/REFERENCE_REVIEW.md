# Reference review — 24 November 2026

This records what was reviewed and what may be learned from each reference.
Both sites are **references only**: no branding, copy, photography, artwork,
layout code or component code has been copied into this project.

## 1. Main content reference — KLB website

URL: `https://klb-website.onrender.com/`

The site was reviewed in the in-app browser. Initial direct HTTP fetches
returned 503 while the Render service was cold-starting; the page was then
opened successfully in Chromium and its internal pages were inspected.

### Pages and information hierarchy reviewed

| Page | What it contains | Useful pattern for the LMS |
|---|---|---|
| `/` | Hero, catalogue search, popular category links, selected titles, collection counts, institutional story timeline, services summary, news, contact prompt, newsletter and accessibility options | Lead with a small number of clear actions; use real counts and concise cards instead of listing every feature |
| `/books/` | Search, filter by collection/level/subject, sort by title/price/new arrivals, 128 title cards with cover, collection, level, title, subject and price | Learner-centric resource discovery: filter by **level, subject, collection** and sort results |
| `/resources/` | Price lists, annual reports, KLB Act, service charter, complaints procedure, procurement guidance, customer application forms and access-to-information request | A single, searchable document library with categories, PDF previews and clear descriptions |
| `/about/` | Vision, mission, core values, history milestones, mandate, leadership, service charter and corporate social value | Institutional information separated into story, mandate, leadership and public accountability |
| `/services/` | Publishing, design/editorial, translation, printing, branding and corporate social value | Present services as discrete cards with a consistent “what / what for / next step” structure |
| `/digital/` | 250+ e-books, four-step buying guide, digital partners, institutional licensing guidance | Explain digital access in short steps; separate individual, school and library routes |
| `/news/` | Dated announcements with categories such as governance, publishing, partnerships, schools and literacy | Announcements belong in a structured, filterable news module, not scattered across pages |
| `/contact/` | Offices, phones, emails, enquiry-type selector, short form, FAQ-style quick answers | Route enquiries by purpose and answer common questions before asking for data |

### Content ideas to incorporate, reorganised for an LMS

- A **Learning Resources** catalogue organised by level, subject, class/grade and
  collection, with search, filters, preview and access links.
- A **Documents & Forms** library for price lists, reports, policies, charters and
  application forms, with category labels and accessible previews.
- An **Announcements** area with dates, categories and audience labels so
  learners, guardians and teachers see what matters to them.
- Concise **institutional information**: who we are, vision, mission, mandate,
  leadership and contact routes, kept separate from the product experience.
- A **digital learning guide** that explains how to find, preview and access a
  resource on a phone, tablet or laptop.
- Accessibility controls and plain-language prompts for low-confidence users.

### Deliberate non-copying

The reference site's logo, colours, exact sentences, photography, cover artwork,
prices, partner marks and source code are not reused. Its information hierarchy
is used only to decide **what information deserves a place in the new product**.

## 2. UI/UX reference — Zeraki

URL: `https://www.zeraki.app/`

### Patterns observed

- Top navigation with a small number of product destinations.
- A strong hero with one primary message and role/product entry points.
- Three product cards with short benefit-led descriptions and direct links.
- Compact institutional proof points: presence, awards and statistics.
- A news strip, newsletter signup and a short demo-interest form.
- Clear footer grouping: contact, social links and legal/organisational links.

### What this means for our product

- Keep navigation shallow: **Public / Learner Portal / Administration** are the
  three top-level experiences; role dashboards live inside the authenticated
  portal.
- Use small, purposeful cards rather than long feature lists.
- Make each dashboard answer three questions: **what is mine, what is due, what
  changed?**
- Use professional photography sparingly and only where it supports meaning.
- Preserve our own identity, palette, copy and component system. Zeraki is a
  polish benchmark, not a source of content or design assets.

## 3. Reference limitations

- The KLB site is informational and commercial; it is not itself a learner
  management system. It supplies **content structure and institutional source
  material**, not workflow design.
- The Zeraki site is a marketing site; its external dashboards were not treated
  as functional specifications. It supplies **presentation discipline** only.
- Neither reference overrides the core objective: organised learner management
  and easier access to educational resources.
