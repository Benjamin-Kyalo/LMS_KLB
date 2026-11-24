# Asset credits

## Photography

The homepage uses four locally hosted photographs downloaded from Unsplash. They
are illustrative stock photos, not pictures of Kenyan Literature Bureau staff,
schools or learners. Attribution is not required by the
[Unsplash License](https://unsplash.com/license), but the source image URLs are
kept here for traceability.

| Local file | Used for | Source image |
|---|---|---|
| `frontend/public/images/hero-students.jpg` | Public hero | `https://images.unsplash.com/photo-1523240795612-9a054b0db644` |
| `frontend/public/images/family-progress.jpg` | Learning workspace card | `https://images.unsplash.com/photo-1758687126375-e2c1683219e9` |
| `frontend/public/images/teachers-lesson.jpg` | School-day workspace card | `https://images.unsplash.com/photo-1509062522246-3755977927d7` |
| `frontend/public/images/digital-library.jpg` | Digital-publishing workspace card | `https://images.unsplash.com/photo-1507842217343-583bb7270b66` |

The images are served from `frontend/public/images` rather than hotlinked, so the
public site does not depend on a third-party CDN at runtime. They were resized
through Unsplash image parameters at download time and are ordinary JPEG files.

## Illustration

`frontend/public/hero-learning.svg` is an original local SVG illustration of
books, connected profiles and charts. It is used in the progress/insights
section and is not derived from the reference site.

## Reference use

`https://www.zeraki.app/` was consulted only for general public-site information
hierarchy: a strong hero, a small number of product areas, a facts strip and
clear role/contact paths. No Zeraki branding, copy, photographs, SVG assets,
layout files or code were copied. All KLB wording, palette, routes and component
implementations are original to this project.
