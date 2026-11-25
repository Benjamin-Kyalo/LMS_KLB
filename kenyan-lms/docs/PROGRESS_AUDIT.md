# Progress audit — 25 November 2026

Status: **implementation pass complete; deployment/runtime sign-off still pending**. No commit or push has been made.

Scope note: the attached PNGs could not be viewed visually in this session, so their exact swatches were extracted programmatically from pixel data. The earlier hero/stats work uses the exact text quoted by the user. The stale “Offline changes queued until reconnected” and sample-count wording came from the managed site-content defaults/editor, not from a live offline queue; the offline/PWA code was removed in an earlier pass.

## Done

| Area | What is now in place | Verification |
|---|---|---|
| Homepage and sign-in photograph | The homepage hero and sign-in story both read `hero.imageSrc` from the managed site-content document. The default is the supplied local `/images/hero-community.png`, with a dark scrim keeping sign-in text legible. | `Home.test.jsx` and `Login.test.jsx` assert the shared default and a runtime override. |
| Admin-editable appearance | `SUPER_ADMIN` and `ADMIN` can replace any managed photo, edit public wording and set safe section styles from **Administration → Appearance**; a custom role needs `admin.access` and `appearance.manage`. Photo uploads use JPG/PNG/WebP, validate extension, bytes and decoded dimensions (≥640×360, ≤5 MB), store under `media/site-content/<slot>/`, publish immediately and write an audit entry. | Focused frontend and backend tests pass, including institution-admin upload, remove, reset, wording and style edits. |
| Permission boundary | Photo endpoints and the site-content PATCH require admin permission; a custom role's picked capabilities are enforced by the backend. Teachers, learners and anonymous users cannot change appearance content. | Backend tests assert `403` for a learner and `400` for invalid files or styles; institution `ADMIN` accounts can edit photos, wording and section styles. |
| Stale stats/offline block removed | The `facts` schema, homepage section, CSS and admin editor fields are gone from frontend and backend defaults. Saved `facts` keys are stripped on read and write. The retired offline phrases are sanitised from old saved content. | `Home.test.jsx` asserts the block is absent; theming tests assert saved `facts` never return. |
| Backend entry point | Plain `python manage.py …` now uses `config.settings`, so `runserver` and `check` work on a fresh checkout. `wsgi.py` and `asgi.py` still default to `config.settings_prod`, which fails closed without production environment values. | `manage.py check` passed with no env override; `check --deploy` passed with placeholder production values. |
| Particle headlines and auth visibility | Home, public login story and registration keep a real `<h1>` under the canvas. Hover repulsion stays gentle, the base heading remains legible, and reduced motion/responsive cleanup are preserved. | Focused particle/auth tests and browser checks passed in the previous pass. |
| Five swatch palettes added *(earlier pass)* | Blue Coral Daylight, Forest Green, Citrus Bloom, Heritage Spice and Bright Horizon were seeded in the admin catalogue from the five attached images. Exact source swatches are preserved; derived 900/800/700 steps pass the admin WCAG check. Ocean Blue remained active at that point. | Focused theming suite passes `15 tests`; migration applied locally and all seven built-ins verified at that point; `makemigrations --check --dry-run` reports no drift. |
| Security hardening | Session cookies + CSRF, lockout/throttles, scoped reads, upload sniffing, security headers/CSP, secret handling and RBAC are in place. | Full backend suite result is recorded in `TESTING_CHECKLIST.md`. |
| Role-model simplification (documented) | Built-ins are `SUPER_ADMIN`, `ADMIN`, `CUSTOM`, `TEACHER`, `LEARNER`, `GUARDIAN`; retired `PLATFORM_ADMIN`, `INSTITUTION_ADMIN`, `SCHOOL_ADMIN` and `CONTENT_MANAGER` accounts migrate to `ADMIN`. Custom roles carry picked capabilities, enter `/admin` only with `admin.access`, and are managed at `/api/auth/roles/`; `/api/auth/users/roles/` lists built-ins plus custom options. Passwords are never changed, generated or printed by the migration. | Documentation updated to the approved contract; new-model test totals are not yet recorded in `TESTING_CHECKLIST.md`. |
| Offline/PWA/native removal | No service worker, manifest, workbox, precache, IndexedDB queue or Capacitor projects remain. | Rebuilt `dist` contains no PWA/service-worker/manifest artifacts. |
| Dependency and build health | Frontend tests, production build and dependency audit are clean. | `101 tests across 32 files`, `npm run build` succeeded, `npm audit --audit-level=moderate` found `0 vulnerabilities`. |
| Repository hygiene | No commit or push was made. Local `.env` remains ignored; its PostgreSQL password is owner-designated and must not be rotated without approval. `backups/` remains ignored because it contains hashes and PII. | `git status --short` confirms working-tree changes only; `git diff --check` reports only LF→CRLF warnings. |
| PostgreSQL password alignment | The project-root `.env` holds the owner-designated password. The PostgreSQL role was aligned once with `scripts/set_postgres_password.ps1`; it must not be rotated again without approval. | Verified a live login using the `.env` value; localhost `scram-sha-256` restored; no secret appears in the script, docs or output. |

## Pending (deployment/runtime, not code completeness)

1. **Production environment**: set a real long `PRODUCTION_SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` and SMTP values. Placeholder `check --deploy` passing is not a deployment sign-off.
2. **Reverse proxy and TLS**: terminate HTTPS, set `X-Forwarded-Proto: https`, and restrict `TRUSTED_PROXY_IPS` so `X-Forwarded-For` cannot spoof lockout IPs.
3. **Media serving**: configure the web server or CDN to serve `/media/` with safe content types. Django serves uploads only in debug mode. Confirm the CSP `img-src` policy matches the chosen image host.
4. **Shared cache and least-privilege DB**: provide a shared cache for throttles and connect the app with a database role limited to the `lms` database.
5. **SMTP reset flow**: send a real password-reset email end to end and confirm links use the production origin.
6. **Old service-worker kill-switch**: serve `/sw.js` for one release with an unregister/self-delete response, or ask existing users to clear site data.
7. **Manual accessibility review**: check the particle headline and admin upload control with a screen reader and keyboard-only navigation.
8. **User confirmation of the screenshot**: the attached image could not be read here; confirm the hero photo and removed block match what was intended.
9. **Palette activation choice (historical)**: at the earlier pass, all five new palettes were available but none had been activated. **Current status (25 November 2026):** `theming.0004_seed_and_activate_plum_harvest` was applied locally; Plum Harvest is the active palette and fresh-install default among eight built-ins. Administrators can still choose another palette in `/admin/theme`.
10. **Commit/push approval**: everything remains uncommitted and unpushed by instruction.

## Improvements worth adding next

- Add a thumbnail preview and alt-text guidance beside the upload control so administrators can see the exact crop before publishing.
- Reuse or delete superseded uploaded files instead of leaving every previous hero photo in media storage.
- Add per-admin upload throttling and an audit-log filter for `site_content.hero_image_uploaded`.
- Generate responsive image sizes or move uploads to a CDN with cache invalidation; the current build still emits one large JS chunk warning.
- Add an end-to-end browser test that uploads a photo, reloads `/`, and confirms the new image loads through the production media path.
- Finish the assistive-technology review and document the exact screen-reader result.
