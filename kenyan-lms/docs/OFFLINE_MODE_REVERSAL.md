# Offline-mode reversal: narrow low-bandwidth web mode

Status: **implemented, off by default**. This document records a deliberate,
narrow reversal of the 24 November 2026 offline removal. It does not restore the
old service worker, PWA shell, broad IndexedDB write queue or native wrapper,
and it does not erase the historical removal record in `TESTING_CHECKLIST.md`,
`PRODUCT_DIRECTION.md`, `MILESTONES_AJ.md` or `NATIVE_WRAPPER.md`.

## What changed and why

The earlier removal was correct for the product direction: a normal web app with
honest failures and no offline claim. Low bandwidth is still a real operating
condition, so this change adds only what can be made safe:

- public, non-personal reads may be cached after a page has loaded;
- a small allowlist of theming writes may be queued when the network fails;
- queued writes use optimistic-concurrency checks and surface conflicts.

There is no offline first load and no navigation while offline. If the page is
not already open, the user still needs a live connection.

## What remains removed

- No service worker is registered. `frontend/public/sw.js` is only an
  unregistered kill-switch for clients that installed the old worker.
- No PWA manifest, workbox precache, native wrapper or native build.
- No persistent offline queue for attendance, assessment, fees, messages,
  learner/guardian records or file uploads.
- No credentials, session cookies, CSRF tokens, bearer tokens or person-like
  fields in browser storage. The cache/outbox use namespaced `localStorage`
  keys under `klb_low_bandwidth_v1`; the client rejects sensitive keys and
  token-like values before queueing.
- No raw CSS, unvalidated links or retired public-site role cards can return
  through a cached response.

## Enablement

All switches are server-side environment variables; there is no generic
feature-flag table and no `VITE_`-prefixed secret. Defaults keep the feature
off or minimal:

| Variable | Default | Purpose |
|---|---|---|
| `OFFLINE_MODE_ENABLED` | `False` | Master switch; when false, the public config reports offline disabled and the browser stores nothing |
| `OFFLINE_READ_CACHE_ENABLED` | `True` | Allow public allowlisted GET caching once the master switch is on |
| `OFFLINE_OUTBOX_ENABLED` | `True` | Allow allowlisted `PATCH`/`DELETE` queueing once the master switch is on |
| `OFFLINE_CONFIG_VERSION` | `1` | Changing it invalidates cached reads; queued writes remain so a retry can reveal a conflict |
| `OFFLINE_CACHE_TTL_SECONDS` | `3600` | Maximum age of a cached public read |
| `OFFLINE_MAX_CACHED_READS` | `25` | Maximum cached paths per browser |
| `OFFLINE_OUTBOX_MAX_ITEMS` | `20` | Maximum queued writes per browser |
| `OFFLINE_CACHE_PATHS` | theming, public books/resources and content facets | Comma-separated public read allowlist |
| `OFFLINE_OUTBOX_PATHS` | `/api/theming/site-content/`, `/api/theming/palettes/` | Comma-separated write allowlist |

Do not add authenticated, guardian-linked, assessment or fee paths to either
allowlist without a separate privacy review and tests. The browser refuses
`POST`, `PUT` and paths outside these lists.

## Client configuration

`GET /api/core/client-config/` is public and returns only booleans, allowlists,
limits and a version. Its shape is:

```json
{
  "version": "1",
  "offline": {
    "enabled": false,
    "service_worker": false,
    "native_app": false,
    "credentials_stored": false,
    "read_cache": {
      "enabled": false,
      "paths": [],
      "max_age_seconds": 3600,
      "max_items": 25
    },
    "outbox": {
      "enabled": false,
      "methods": ["PATCH", "DELETE"],
      "paths": [],
      "max_items": 20
    }
  }
}
```

The response is `Cache-Control: public, max-age=300`; it contains no user,
institution, permission or profile data.

## Writes and conflicts

`api.patch()` and `api.del()` accept `{ ifMatch }` and send it as `If-Match`.
Server-side stale-write checks build on `ConflictAwareMixin`; a stale write
returns HTTP 409 with:

```json
{
  "code": "conflict",
  "message": "This record changed since you loaded it.",
  "server": {
    "id": 12,
    "updated_at": "2026-11-26T20:00:00Z",
    "data": {}
  }
}
```

The `server.data` copy is only returned for records whose serializers are safe
for the caller; creates have no server copy, so broader create replay remains
out of scope. The `/admin/offline` and `/portal/offline` screens show status,
queued writes, conflicts and explicit retry/remove controls. Themes use
`/api/theming/site-content/` and `/api/theming/palettes/`; their write views
now participate in the same check.

## Operator checklist

1. Leave `OFFLINE_MODE_ENABLED=False` unless the low-bandwidth benefit is
   needed and the allowlists have been reviewed.
2. Keep secrets server-side. Never expose an offline path or config value with
   a `VITE_` prefix.
3. Keep the old service-worker kill-switch in the deployment for one release:
   serve `/sw.js` with `Cache-Control: no-cache`.
4. Verify browser storage contains no password, token, CSRF, session, email,
   phone, admission or other person-like field.
5. Verify a stale queued write produces a visible 409 conflict and never
   overwrites newer server state.
6. Do not claim full offline operation; this is a narrow cache/outbox for an
   already-loaded page.

## Verification

Focused backend coverage lives in `apps.core.tests.test_low_bandwidth` and the
theming stale-write tests; frontend coverage lives in
`src/services/lowBandwidth.test.js`, `src/services/api.test.js` and
`src/pages/LowBandwidth.test.jsx`. Current results are recorded in
`TESTING_CHECKLIST.md`.
