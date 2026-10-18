# Reliability and the 99% uptime target

The initial service objective is 99% availability over a rolling 30-day window. A time-based 99% objective permits 7 hours 12 minutes of unavailable time in 30 days. It is an operating target; a contractual SLA requires an explicit agreement and remedy terms.

## Service indicators

Measure the public website, authenticated API and asynchronous work separately. Website probes must check expected content over public HTTPS. API probes check readiness and a controlled authenticated read. Track valid-request success, p50/p95/p99 latency, database pool saturation, queue depth/oldest age, worker heartbeat, lease recovery and delivery reconciliation.

Define availability as good eligible events / all eligible events for request-based measurement, or good probe intervals / all scheduled intervals for time-based measurement. Do not interchange these denominators. Include eligible timeouts, 5xx and legitimate in-envelope 429s as failures. Exclude intentionally invalid/unauthorized requests consistently. Count planned maintenance against the initial objective; document any later contract-specific treatment. Report monitoring gaps as unknown coverage, never assumed uptime.

## Error budget and response

Review the rolling window at least weekly. Alert on sustained outage and fast/slow error-budget burn using independent probes where available. When the budget is exhausted, prioritize reliability fixes, reduce risky releases and require recovery evidence before resuming changes. Record detection, impact, mitigation, restoration and corrective actions for incidents. Publish customer-relevant status without sensitive infrastructure details.

## Dependency and recovery limits

The initial shared-host architecture has single-host/database dependency risk. Process restart and backups reduce recovery time but do not provide multi-zone failover. Local AI job latency has a separate queue/completion objective and must not make an otherwise healthy API appear ready for unlimited submissions.

Initial proposed recovery objectives are RPO ≤24h and RTO ≤8h. Production timings and actual retained backup intervals must be recorded before claiming achieved recovery. A future multi-zone 99.9% objective allows 43m12s in 30 days and requires tested failover, dependency redundancy and funded operations.

Reference: [Google SRE: implementing SLOs](https://sre.google/workbook/implementing-slos/), [error-budget policy](https://sre.google/workbook/error-budget-policy/).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
