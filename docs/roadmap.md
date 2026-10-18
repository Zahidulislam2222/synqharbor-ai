# Delivery roadmap

The current release implements the frontend and bounded authenticated drafting/review
and Python coding/test/approved-Git workflows. Production evidence is recorded per
release. General connectors, autonomous scheduling, administrator MFA, database
RLS, customer-data legal readiness and large-scale capacity remain explicit gates.
See [core workflows](core-engine.md) and [release acceptance](release-checklist.md).

The authoritative detailed roadmap is [BUILD-PLAN.md](../BUILD-PLAN.md), which
contains ten phases, five parallel workstreams per phase, deploy/rollback gates
and 57 specified acceptance scenarios. A specified scenario is not a passing test.

| Phase | Focus | Delivery gate |
|---|---|---|
| 1 | Foundation and deployment | Public/private boundaries, CI, restore and configuration verified |
| 2 | Identity and secure tenancy | Tenant/role isolation and real authentication flows pass |
| 3 | Collaboration and durable controlled execution | Messages, tasks, attempts and reconnect/recovery pass |
| 4 | Tasks, artifacts and approvals | Exact-version decisions and stale-action refusal pass |
| 5 | One bounded execution route | Qualified local/provider execution and isolated runner pass |
| 6 | Client delivery | Protected tests, independent review and authorized release receipt |
| 7 | Scoped knowledge | Retrieval, citations and downloads enforce audience permissions |
| 8 | Schedules and business workflows | Retry/overlap/idempotency and external-write recovery pass |
| 9 | Client operations and portability | Budgets, backups, exports, handover and operational checks |
| 10 | Production qualification and expansion | Security, reliability, capacity and selected capabilities verified |

Every phase coordinates frontend, backend, agent/integration, infrastructure and
quality work. Every phase ships a scoped increment with rollback; exit criteria
are verified in the intended environment before that phase is marked complete.

## Cloud and hybrid delivery direction

Prioritize qualified AWS, GCP and Azure components within verified free allowances,
using the existing host for suitable costly or compute-heavy work. Preserve the
current authorized deployment while cloud account/plan eligibility, native resource
inventories, data boundaries, dependency costs and migration/rollback gates are
assessed. See [cloud roles and cost boundaries](cloud-costs.md). Future distributed
control/inference paths need secure adapters and their own workload qualification;
this roadmap enables no automatic paid fallback.
