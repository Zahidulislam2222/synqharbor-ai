# SynqHarbor AI

**One workspace. Human-led. Agent-powered.**

A self-hostable collaboration and controlled AI delivery platform maintained by
**[Zahidul Islam](https://github.com/Zahidulislam2222)**.

[Website](https://synqharbor.zahidul-islam.com/) · [Application](https://synqharbor.zahidul-islam.com/control/) · [Documentation](docs/README.md) · [Roadmap](docs/roadmap.md)

![SynqHarbor harbor artwork](public/media/harbor.webp)

## Core workflows

- Authenticated workspaces, memberships, messages, tasks and selected source documents.
- Cited drafting through bounded local AI work and a separate Reviewer context.
- Operator-approved Python repository proposals, protected multi-file gVisor tests and review evidence.
- Immutable artifact hashes, distinct client/developer approvals and recorded delivery.
- Atomic Git publication at the approved base, installed commit hooks and reconciliation after uncertain interruption.
- PostgreSQL migrations, durable worker claims/leases, revocation/stop controls and downloadable delivery reports.
- Responsive frontend, self-hosted assets, reduced-motion support and automated quality/security checks.

`/control/` uses saved API records. `/workspace/` is a separate browser-local
interface whose state resets on reload. Account enrollment is operator-managed.
The bounded execution route supports approved Python profiles and dedicated Git
repositories. Broader connectors, tenant RLS, administrator MFA and distributed
execution remain explicit [roadmap gates](docs/roadmap.md).

## Run frontend and backend

Use Node.js 24 LTS, Python 3.12 and PostgreSQL. Copy safe settings from
`.env.example` into private environment files. Public-prefixed values are embedded
in the browser; never place credentials there.

```sh
npm ci
npm run dev
python3 -m venv .venv-api
.venv-api/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv-api/bin/python -m app.database
../.venv-api/bin/python -m app.manage create-user --email USER_EMAIL --name USER_NAME
../.venv-api/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
# Separate supervised process:
../.venv-api/bin/python -m app.worker
```

Local HTTP requires its own non-Secure cookie name and exact configured origin.
Production uses HTTPS and secure host cookies. Configure installed local model
digests and a checksum-qualified runner before enabling execution. See
[self-hosting](docs/self-hosting.md), [core setup](docs/core-engine.md),
[configuration](docs/configuration.md) and [deployment templates](infra/README.md).

## Verify

```sh
npm test
npm run typecheck
npm run lint
npm run build
cd backend
../.venv-api/bin/python -m pip install -r requirements-dev.txt
../.venv-api/bin/python -m pytest -q
../.venv-api/bin/ruff check app runner migrations tests
../.venv-api/bin/mypy app
```

CI runs frontend/backend quality, dependency audits and Gitleaks/Bandit/Semgrep
security checks. Actual model quality, sandbox behavior, production workflows,
restart and encrypted restore require their own environment-specific checks.
Read the [release checklist](docs/release-checklist.md) and [changelog](CHANGELOG.md).
The [readiness record](docs/readiness.md) identifies remaining operating gates,
their consequences and the maintainer responsible for them.

## Public documentation

| Topic | Guide |
|---|---|
| System and boundaries | [Architecture](docs/architecture.md), [API](docs/api.md), [core workflows](docs/core-engine.md) |
| Installation and configuration | [Self-hosting](docs/self-hosting.md), [configuration](docs/configuration.md), [backend](backend/README.md) |
| Security and reporting | [Threat model](docs/security.md), [SECURITY.md](SECURITY.md) |
| Privacy, law and responsible AI | [Privacy](docs/privacy.md), [cookies](docs/cookies.md), [processing](docs/data-processing.md), [legal readiness](docs/legal-readiness.md), [terms](docs/terms.md), [acceptable use](docs/acceptable-use.md) |
| Reliability and recovery | [99% objective](docs/reliability.md), [operations](docs/operations.md), [disaster recovery](docs/disaster-recovery.md) |
| Future 1M+ simultaneous users | [Scale architecture](docs/scalability.md), [performance qualification](docs/performance-testing.md), [cost boundaries](docs/cloud-costs.md) |
| Delivery and accessibility | [Roadmap](docs/roadmap.md), [ten-phase build plan](BUILD-PLAN.md), [accessibility](docs/accessibility.md) |
| Shareable overview | [Technical overview](docs/technical-overview.md), [PDF](public/documents/SynqHarbor-AI-Technical-Overview.pdf) |

The **99% rolling-30-day availability objective** and future **1M+ simultaneous-user
envelope** have documented workload, qualification, operational and funding gates.
Scale is an architectural target; release-specific measurements establish actual
capacity. Applicable legal duties depend on the operator, market, data and use.

## Structure

```text
src/              Next.js routes, React interfaces, public settings and JSON copy
backend/app/      FastAPI, durable worker, sessions, approvals and Git control
backend/runner/   Protected Python harness executed inside gVisor
backend/data/     Maintained prompts, specifications and repository profiles
backend/migrations/ Frozen Alembic migrations
backend/tests/    Automated backend regression suite
tests/            Automated frontend regression suite
docs/             Public engineering, policy and operating documentation
infra/            Portable frontend/backend deployment templates
.github/          Public CI, issue templates and contribution workflow
```

## Ownership, contribution and license

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
and [SECURITY.md](SECURITY.md). Community support has no contracted response-time
SLA. Never put confidential data in public issues.

Source is [Apache 2.0](LICENSE). Dependencies, models and fonts retain their own
licenses; see [third-party notices](THIRD-PARTY-NOTICES.md). Credentials, deployment
access details, private recovery records and operator documents are excluded from
public source.
