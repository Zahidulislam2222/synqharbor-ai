# Architecture

The release combines a static Next.js frontend with a same-origin FastAPI control plane, PostgreSQL ledger, separate durable worker, local Ollama inference and rootless gVisor execution. The web process never executes submitted code. `/control/` uses authenticated persisted records. `/workspace/` maintains separate browser-tab-local interaction state, cleared on reload.

## Trust boundaries

| Boundary | Enforcement |
|---|---|
| Browser → API | HTTPS, opaque HttpOnly Secure host cookie, SameSite=Lax, exact Origin and synchronizer CSRF token |
| User → workspace | Membership and role checked on each protected request; inaccessible objects return 404 |
| Task → run | Revision, explicit criteria, selected source IDs, bounded dispatch and idempotency |
| Worker → model | Loopback local-only endpoint, complete installed model digest verification, separate Builder/Reviewer contexts |
| Worker → code | Fresh gVisor process per protected case, empty environment, read-only code/rootfs, no network or host credentials |
| Approval → release | Immutable artifact hash and revision, distinct client/developer accounts, operator repository grant, pinned Git base |
| Runtime → database | Separate migration identity; runtime cannot own tables/schema, CREATE schema or bypass row security |

## Durable work

PostgreSQL owns run claims, leases, attempts, artifacts, approvals, audit events, delivery intents and receipts. Model calls occur outside database transactions. Fencing and revision checks prevent stale workers from publishing. Workspace stop, source/member revocation and repository grant changes serialize with publication. An acknowledged change prevents subsequent publication or waits for the bounded in-flight operation.

Git preparation occurs in an isolated clone with installed hooks. Publication compares the expected reference atomically and uses the native index lock. An uncertain post-publication result stays reserved for read-only reconciliation. Dedicated operator-owned repositories must not be edited manually during installation.

## Operational boundaries

Project-specific services, users, storage, private listeners, resource limits and versioned releases isolate the application on shared infrastructure. General shell execution, arbitrary languages, automatic deployment to customer infrastructure, remote providers and external publishing connectors require additional engineering and authorization. Tenant RLS, administrator MFA and multi-region failover remain roadmap gates; application authorization and restricted database roles are the present boundary.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
