# Asset credits

## Photography

The site uses eleven locally hosted photographs: seven supplied by the project
owner and four illustrative stock photos downloaded from Unsplash. Eight are
active defaults and three are retained assets. The stock photos are not pictures
of Kenyan Literature Bureau staff, schools or learners. Attribution is not
required by the [Unsplash License](https://unsplash.com/license), but the source
image URLs are kept here for traceability.

| Local file | Used for | Source image |
|---|---|---|
| `frontend/public/images/hero-community.png` | Homepage hero | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/workspace-skill.jpg` | Learning workspace card | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/workspace-education.jpg` | School-day workspace card | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/insight-success.jpg` | Progress insight panel | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/signin-time.jpg` | Sign-in story | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/register-learn.jpg` | Registration story | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/tutor-brain.jpg` | Learner/parent tutor workspace | Supplied by project owner, 25 November 2026 |
| `frontend/public/images/digital-library.jpg` | Digital-publishing workspace card | `https://images.unsplash.com/photo-1507842217343-583bb7270b66` |
| `frontend/public/images/hero-students.jpg` | Retained asset; no longer active | `https://images.unsplash.com/photo-1523240795612-9a054b0db644` |
| `frontend/public/images/family-progress.jpg` | Retained asset; no longer active | `https://images.unsplash.com/photo-1758687126375-e2c1683219e9` |
| `frontend/public/images/teachers-lesson.jpg` | Retained asset; no longer active | `https://images.unsplash.com/photo-1509062522246-3755977927d7` |

All active photo slots are administrator-changeable from **Appearance →
Photos**; uploading a file publishes it immediately. The images are served from
`frontend/public/images` rather than hotlinked, so the public site does not
depend on a third-party CDN at runtime. The stock images are ordinary JPEG
files; the supplied hero photograph is a PNG. The two small reference images
`skill 2.jpg` and `image.png` were not used because they do not meet the
managed-photo dimensions.

## Library artwork

`frontend/public/images/library/covers/` contains 13 original typographic book
covers and `frontend/public/images/library/thumbnails/` contains 12 original
subject thumbnails. They were generated locally for this project from plain
title and subject text; no publisher cover image, book page image or third-party
thumbnail was copied or hotlinked. They are served from the frontend's public
folder, so `/library` has no runtime dependency on an external image host.

The public catalogue records that use this artwork were replaced by
`backend/apps/content/migrations/0003_public_library_thumbnails.py`. Book
metadata was checked against the [Open Textbook Library](https://open.umn.edu/opentextbooks/)
API, and resource records point to public pages from OpenStax, Open Book
Publishers, Portland Community College, the Kenya Institute of Curriculum
Development and the Kenya Education Cloud. The resource pages are links only;
their text, logos and images are not republished here.

### OpenStax licensing (rechecked 26 November 2026)

OpenStax changed its default licence in April 2026: newly released and updated
titles are generally **CC BY-NC-SA 4.0 International**, with limited exceptions.
Check the licence on each individual book page before copying anything. Key
points from the [OpenStax licence page](https://openstax.org/license/) and
[licensing announcement](https://openstax.org/blog/openstax-licensing):

- Attribution: reproduce the book's own **Citation/Attribution** block, which
  includes the "Access for free at …" link. Credit OpenStax, the title and the
  free version on every page or digital equivalent where content is reused.
- OpenStax-owned images, activities and assessments carry the same CC BY-NC-SA
  terms; third-party media may have its own caption credits, which must be kept.
  Uncredited OpenStax art uses "Copyright Rice University, OpenStax, under CC
  BY-NC-SA 4.0 license."
- Noncommercial reuse, adaptation, remixing and translation are allowed if
  derivatives use the same licence. Commercial redistribution and AI/LLM
  training require permission through the
  [OpenStax reuse request form](https://riceuniversity.tfaforms.net/52).
- OpenStax logos, covers and the Rice/OpenStax names are excluded and need
  written consent. No Kenya-specific exception was found; 4.0 International
  applies.

Further references: [OpenStax FAQ](https://openstax.org/faq),
[Terms of Use](https://openstax.org/tos),
[Licensing information help article](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks),
[Commercial use guidance](https://help.openstax.org/s/article/Commercial-use-under-the-Creative-Commons-License),
and the [licence deed](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Nothing has been copied into the platform yet, so no new attribution notices are
required at this time.

## Illustration

`frontend/public/hero-learning.svg` is an original local SVG illustration of
books, connected profiles and charts. It is retained but is no longer used in
the progress/insights section, which now uses an administrator-managed photo.
It is not derived from the reference site.

## Reference use

`https://www.zeraki.app/` was consulted only for general public-site information
hierarchy: a strong hero, a small number of product areas and clear role/contact
paths. The earlier facts strip was removed at the user's request. No Zeraki
branding, copy, photographs, SVG assets,
layout files or code were copied. All KLB wording, palette, routes and component
implementations are original to this project.
