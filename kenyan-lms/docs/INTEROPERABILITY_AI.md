# Interoperability and governed AI groundwork

Status: **read-only groundwork implemented**. These features add controlled
integration surfaces without introducing new dependencies, changing CSP, or
creating credentials in source control.

## OneRoster read endpoints

Base path: `/api/integration/oneroster/v1p1/`.

| Method | Endpoint | Required scope | Records |
|---|---|---|---|
| GET | `courses/` | `courses.read` | Published courses in the pinned institution |
| GET | `classes/` | `classes.read` | Published courses shaped as classes |
| GET | `users/` | `users.read` | Active learners and teachers in the pinned institution |
| GET | `enrollments/` | `enrollments.read` | Teacher course ownership plus learner participation derived from progress/submissions |
| GET | `orgs/` | `orgs.read` | The pinned active institution |

Responses are OneRoster-shaped (`sourcedId`, `status`, `classCode`, `paging`,
and so on) but are derived from existing LMS records. They are institution-scoped
and read-only: `POST`, `PATCH`, `PUT` and `DELETE` are not accepted. `limit` is
bounded by `ONEROSTER_MAX_PAGE_SIZE`, and reads are throttled per client id by
`ONEROSTER_THROTTLE_RATE`. Every successful read writes an
`integration.oneroster.read` audit row with the client id, scope, paging values
and counts — never a secret or person-like payload.

## Client configuration and assertions

Clients are configured only in the server environment with
`KLB_ONEROSTER_CLIENTS`. No client id, secret or institution pin reaches the
browser or the repository. The JSON shape is:

```json
{
  "sis-client": {
    "secret": "server-side-secret",
    "institution_id": 1,
    "scopes": ["courses.read", "classes.read", "users.read", "enrollments.read", "orgs.read"]
  }
}
```

Each client calls with a short-lived `Authorization: Bearer <assertion>`
header. The assertion is a stdlib HMAC-SHA256 (HS256) JWT with `iss`/`sub` set
to the client id, `aud` set to `KLB_ONEROSTER_AUDIENCE`, and bounded `iat`,
`nbf`, `exp` and optional `jti`. `KLB_ONEROSTER_TOKEN_TTL_SECONDS` limits the
claimed lifetime. Invalid signatures, unknown clients, wrong audience, expired
or over-long tokens and any algorithm other than HS256 are all rejected with
the same generic 401 message. A client can read only its pinned institution and
only the scopes assigned to it.

This is deliberately **not** an OAuth token endpoint: the application does not
issue bearer tokens at login and does not expose a token exchange route.

## Explicitly unsupported protocols

The following paths exist only to return a short, generic 403 and an
`integration.unsupported.rejected` audit row:

- `/api/integration/lti/launch/`
- `/api/integration/oidc/`
- `/api/integration/jwks/`
- `/api/integration/oauth/token/`

LTI 1.3 launches, OIDC discovery, JWKS key sets, RS256 verification and OAuth
token endpoints are not implemented. CSP `connect-src` stays `'self'`; an
external SIS or AI host requires a deliberate, reviewed production override.
Do not enable the unsupported routes by loosening existing permissions.

## Governed curriculum tutor

The tutor remains local and deterministic by default. An optional HTTP adapter
is configured only through `KLB_TUTOR_PROVIDER`, `KLB_TUTOR_API_URL`,
`KLB_TUTOR_API_KEY` and `KLB_TUTOR_ALLOWED_HOSTS`. It is HTTPS-only, refuses
redirects, query strings, userinfo and fragments, sends no learner or
assessment records, and accepts remote text only as a verbatim substring of the
local grounded answer. `TutorThrottle` still governs the ask action.

Safe policy metadata is returned by:

- `GET /api/tutor/conversations/health/` — provider, grounded-only flag and
  `policy`;
- tutor message payloads — the same `policy` block on each answer.

The policy includes a version, allowed curriculum sources, excluded record
classes, the verbatim-answer rule, maximum question length and whether an
external provider is configured. It never includes an API key, URL, question or
answer. The learner-facing workspace displays the policy version and a short
plain-language summary.

`ask()` now writes explicit `tutor.answer.requested` and `tutor.answer.generated`
audit rows with the conversation reference, provider name, policy version and
(where available) grounding result. The request row is written before any
provider call, so a failed provider attempt is still visible. The details
deliberately exclude the question, answer and any secret.

## Operational limits

- Client secrets and tutor credentials are environment variables only; keep
  them server-side and never give them a `VITE_` prefix.
- A shared cache is required for consistent throttling across workers;
  see `PRODUCTION_CONFIGURATION.md`.
- Recurring SIS synchronisation is not scheduled: there is no scheduler
  dependency and no background sync. Use an approved external scheduler only
  after a separate design review.
- No migration was added for interoperability or governance metadata.
