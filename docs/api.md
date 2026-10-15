# API roadmap

The current website has no deployed application API. No account, connector, inference or release request is issued by the browser. The public source documents the future contract.

## Current interfaces

The current website has no deployed application API. No account, connector, inference or release request is issued by the browser. The public source documents the future contract.

## Planned API domains

Identity and sessions; organizations and membership; rooms and messages; tasks and runs; artifacts and approvals; connector grants; usage and schedules. OpenAPI will be generated from implemented routes.

## Contract requirements

Tenant scope and role checks apply to every object access. Unsafe requests require CSRF/origin protection. Input bounds, pagination, optimistic revisions, idempotency and structured errors are part of endpoint acceptance criteria.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).
