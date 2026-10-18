# Release scope and readiness

Release 0.3.0 is an operator-managed website and bounded AI delivery application.
Qualification uses synthetic tasks and a dedicated repository. Account enrollment
is closed to public self-service. This release does not establish customer-scale
capacity, a contractual service level or readiness for regulated data.

The maintainer and operational owner is **Zahidul Islam**. A Verified status means
the named check ran in its stated environment; a Deferred or Unverified requirement
is not a passed check. Release-specific evidence and hosted check results accompany
the [GitHub releases](https://github.com/Zahidulislam2222/synqharbor-ai/releases).

| Requirement | Status | Evidence or remaining gate |
|---|---|---|
| Automated backend behavior | Verified | 87 cases pass with SQLite and dedicated PostgreSQL parity; includes authorization, stale/duplicate decisions, revocation, worker fencing and recovery |
| Automated frontend behavior | Verified | 21 regression cases; TypeScript, lint and static export pass |
| Dependency and source scanning | Verified | Current installed dependency audits and Gitleaks, Bandit and Semgrep pass; these checks do not certify application security |
| Real deployed model, browser and approved delivery journeys | Verified | Both supervised HTTPS workflows pass with distinct approvals and exact reports; coding passes five protected tests and exact Git publication. Nine isolated Chromium checks include create/join privacy, persistence, keyboard use, account switching and three accessible layouts. Headless tab activation uses an explicit focus event. |
| Encrypted off-host production restore | Verified | Production archive restored into an isolated database with all 21 tables matching by row/hash; both exact workflow reports, artifacts and approvals survive service restart. This is a controlled drill, not host-loss failover. |
| 99% rolling-30-day availability | Unverified | Operating target; no qualified 30-day measurement or contractual SLA |
| Representative load, viral bursts and recovery | Deferred | No measured user/RPS capacity; qualify staged admission envelopes before expansion |
| Correlated request telemetry, dashboards and delivered alerts | Deferred | Health checks, service logs and run audit events exist; aggregate latency/error/saturation and actual alert delivery/triage need qualification |
| Scheduled backup retention, stale-backup alerts and recurring upkeep | Deferred | A manual restore drill does not prove an unattended backup service |
| Host/zone resilience | Deferred | The initial service has a single-host/database failure domain; no high-availability claim |
| Customer-data legal and organizational controls | Deferred | Complete jurisdiction/vendor/contract assessment, admin MFA, retention/rights/erasure processes and operational controls before customer enrollment |
| Kubernetes, microservices and Redis execution | Not applicable | Not selected for this release; multiple processes/containers do not establish microservices |

Zahidul Islam owns deferred operational/security work **before customer enrollment
or unattended operation**, and capacity/redundancy work **before expanding admission
or making corresponding commitments**. Consequences are restricted enrollment,
manual supervision, single-host outage risk and no measured large-scale guarantee.
A future operator must explicitly accept ownership and complete the relevant gates.

The [scalability plan](scalability.md), [performance qualification](performance-testing.md),
[reliability policy](reliability.md), [recovery runbook](disaster-recovery.md),
[operations](operations.md) and [legal readiness](legal-readiness.md) define the
workloads, proposed latency/error/RPO/RTO objectives and evidence required next.
No new paid capacity or automatic cloud migration is authorized by these targets.
