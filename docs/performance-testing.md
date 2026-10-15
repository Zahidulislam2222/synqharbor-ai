# Capacity qualification and performance testing

The future target is more than 1M simultaneously connected users. Connections,
active requests, retained data and executing agent jobs are different workloads.
No current authenticated million-user capacity is asserted.

## Proposed workload envelope

| Dimension | Planning assumption |
|---|---|
| Concurrent connections | 1,000,000 |
| Active fraction | 10% |
| API requests per active user | 0.2/second |
| Sustained API rate | 20,000 requests/second |
| Burst qualification | 40,000 requests/second |
| Gateway memory illustration | 20KB/connection≈20GB before TLS/application overhead |
| Agent arrivals | 1% submitting once/hour≈2.78 jobs/second |
| Agent concurrency | At 180-second mean duration, approximately 500 jobs |

These are assumptions to test. Size nodes from measured throughput and target
utilization, then include replication, availability and operating headroom.

## Stages and pass/fail gates

Qualify 1K, 10K, 100K and 1M connections progressively. Each stage needs a representative
read/write mix, tenant skew, realistic artifacts, fan-out, reconnect storm, spike,
soak and dependency-failure scenario. Validate data integrity and revoked access.

Proposed initial API thresholds: p95≤500ms and p99≤1500ms for defined interactive
operations; error ratio≤1% under the qualified envelope; no lost accepted writes
or stale authorization. Agent jobs need separate queue-age/completion budgets.
These thresholds are design targets, not recorded measurements.

Use distributed k6 generators, record generator CPU/network saturation and dropped
iterations, and make threshold failures fail CI. A saturated generator invalidates
the apparent server result. Large load tests require their own approved cost and
environment plan; never stress the shared host or third-party services by default.

References: [AWS load-test planning](https://docs.aws.amazon.com/prescriptive-guidance/latest/load-testing/test-types.html),
[k6 thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/),
[k6 metrics](https://grafana.com/docs/k6/latest/using-k6/metrics/reference/).
