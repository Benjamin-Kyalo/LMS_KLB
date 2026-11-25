# Native wrapper removed

**Superseded — 24 November 2026.** The product direction changed: this is a
**normal web app only**. There is no Capacitor wrapper, no native app and no
offline/PWA support.

The former Capacitor configuration, `mobile:*`/`cap:*` scripts, dependencies,
service worker/PWA plugin and the `frontend/android` / `frontend/ios` project
directories were deleted. `npm run build` produces only `index.html`, hashed
CSS/JS assets, `robots.txt`, SVG marks and local images.

Earlier notes about `mobile:sync`, scaffolded Android/iOS projects or a future
signed APK/IPA were accurate for an earlier milestone but no longer describe
the repository. Do not use them as build instructions.

If an existing install still has the old service worker, that is a deployment
cleanup task, not app code: serve `/sw.js` with no-cache and an
unregister/self-delete response for one release, or ask users to clear site
data. Failed mutations now show an error and remain unsaved, and uploads need
a live connection. See `README.md` and `PRODUCTION_CONFIGURATION.md`.
