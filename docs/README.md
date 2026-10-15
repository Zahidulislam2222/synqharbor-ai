# Public documentation

SynqHarbor AI is maintained by **Zahidul Islam**. Current capabilities, operating
objectives and future architecture are documented separately.

[Download the verified 12-page technical overview](../public/documents/SynqHarbor-AI-Technical-Overview.pdf).

To reproduce it, install `requirements-docs.txt` and run:

```bash
python scripts/render-overview.py docs/technical-overview.md public/documents/SynqHarbor-AI-Technical-Overview.pdf
```

| Guide | Covers |
|---|---|
| [Technical overview](technical-overview.md) | Product, ownership, architecture, operations and long-term direction |
| [Architecture](architecture.md) | Current static deployment and planned control-plane/execution boundaries |
| [Self-hosting](self-hosting.md) | Installation, public configuration, deployment, validation and rollback |
| [API roadmap](api.md) | Planned contracts; no deployed collaboration API is claimed |
| [Security architecture](security.md) | Identity, permissions, artifacts, isolated execution and verification |
| [Privacy](privacy.md) | Actual website processing and future responsibilities |
| [Terms](terms.md), [Acceptable use](acceptable-use.md), [Cookies](cookies.md) | Website/software use and browser behavior |
| [Data processing](data-processing.md) | Controller/operator responsibilities, retention, exports and transfer assessment |
| [Reliability](reliability.md) | 99% initial objective, measurement, error budgets and support |
| [Disaster recovery](disaster-recovery.md) | Backup scope, restore verification and proposed RPO/RTO |
| [Scalability](scalability.md) | Future 1M+ connected-user envelope and architecture stages |
| [Performance testing](performance-testing.md) | Workload assumptions, qualification steps and acceptance thresholds |
| [Cloud costs](cloud-costs.md) | Existing-host startup and qualified AWS/GCP/Azure free surfaces |
| [Operations](operations.md) | Local-first deployment, parity, monitoring and recovery |
| [Roadmap](roadmap.md) | Ten phases, parallel disciplines and deployment gates |
| [Accessibility](accessibility.md) | WCAG target, verification boundaries and feedback |

Publication excludes credentials, private project records and unshipped backend
work. Source-license terms are in [LICENSE](../LICENSE); third-party notices are
in [THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md).
