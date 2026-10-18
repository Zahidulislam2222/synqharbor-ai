# API contract

The authenticated control plane uses `/api/v1`. Its exact machine-readable contract is `GET /api/v1/openapi.json`. `/api/v1/health` checks database connectivity and migration head; inference and sandbox qualification are separate readiness checks.

## Authentication

1. `GET /auth/session` establishes an anonymous HttpOnly cookie and returns a CSRF token.
2. `POST /auth/login` accepts email/password with `Origin` and `X-CSRF-Token` headers; successful authentication rotates the session.
3. Preserve the returned CSRF token for subsequent mutations. `POST /auth/logout` revokes the session.
4. `POST /auth/register` is controlled by `SH_REGISTRATION_ENABLED`. The hosted release uses operator-managed account creation.

Never store the session cookie in JavaScript, URLs or localStorage. Cross-origin writes and missing/stale CSRF tokens are refused. Passwords are Argon2 hashed. Email ownership verification, self-service password recovery and administrator MFA are future work; operators create/recover accounts through a private verified process.

## Resources

| Family | Responsibilities |
|---|---|
| `/workspaces`, `/workspaces/{id}/state` | Membership-filtered spaces and saved collaboration state |
| `/invitations/accept`, workspace invitations/members | Expiring role invitations and member revocation |
| Workspace tasks/messages/preferences | Validated collaboration, task revisions and per-account preferences |
| Workspace sources/repositories/execution | Scoped knowledge, operator-granted repository visibility and stop state |
| Task runs, workspace runs | Explicit draft/code submission, bounded durable processing and cancellation |
| Task artifacts and approvals | Immutable version/hash review and distinct actor decisions |
| Workspace deliveries | Authorized delivery intent, receipt, downloaded evidence and interrupted release reconciliation |
| `/capabilities` | Configured inference/execution availability; configuration alone is not a successful job |
| `/contact` | Authenticated, bounded contact record; no outbound email delivery is implied |

Inspect OpenAPI for exact methods, schemas and paths. All writes require session/CSRF validation; object access additionally requires workspace membership and the appropriate role. Repository grants have no self-authorizing HTTP route.

## Limits, errors and compatibility

The v1 wire contract limits names to 80 characters, titles to 100, ordinary text to 4,000, artifacts to 20,000 and criteria to 20. Passwords require 12–128 characters. Settings own body, list, task/source/run quotas and request budgets. Responses use stable error codes, including 401 authentication, 403 permission/CSRF, 404 inaccessible objects, 409 stale/conflicting work, 422 invalid input, 429 exhausted budget and 503 unavailable readiness. Lists are bounded, not an unbounded historical export API.

Mutations use task revisions and action request keys where supported. Reusing keys cannot create duplicate consequential actions. Following a timeout, inspect the recorded run/delivery before retrying. Breaking wire-contract changes require a new API version and migration notes.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
