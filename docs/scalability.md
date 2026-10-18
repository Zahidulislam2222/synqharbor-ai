# Scaling toward 1M+ simultaneous users

One million simultaneous users is the future design envelope. Connected users, actively interacting users, API requests and running AI jobs consume different resources. The present single-host release has no measured million-user capacity.

## Workload assumptions

| Dimension | Planning envelope |
|---|---|
| Simultaneously connected sessions | 1,000,000 |
| Interactive active fraction | 10% ordinarily; also qualify a 100% active stress scenario |
| API rate per active user | 0.2 requests/second |
| Ordinary sustained API load | 20,000 requests/second |
| Fully active equivalent | 200,000 requests/second before burst multiplier |
| Initial burst hypothesis | 2× sustained for 5 minutes; separately test reconnect storms |
| Initial interactive objective | p95 ≤500ms, p99 ≤1,500ms for a defined endpoint mix |
| AI work | Separate admitted-job and token-throughput budgets; connected users do not imply one running model per user |

These are planning assumptions. Validate read/write mix, tenant skew, payload distribution, data size, cache hit ratio, event fan-out, geographic latency and burst duration before sizing. The current control UI polls every three seconds and rechecks identity around private batches; at one million tabs this is unsuitable. Replace polling with authorized push/invalidation, cursor-based deltas, jitter and backoff before that stage. Preserve account-switch privacy guarantees.

## Architecture stages

| Stage | Engineering and exit evidence |
|---|---|
| 500–1,000 normal users | Measure actual simultaneously active fraction; bounded API/worker/database pools, admission control, queue age, restore drill and workload baseline |
| 10K simultaneous | Stateless API replicas, shared durable authority, connection pooling, indexed queries, tenant quotas and event gateway qualification |
| 100K simultaneous | Regional cells, tenant-aware routing, object storage for large artifacts, caching only public material, connection/fan-out budgets and dependency quota validation |
| 1M+ simultaneous | Multiple qualified cells/regions, explicit residency routing, hot-tenant isolation, failover/reconnect drills and distributed load evidence at the chosen active-user mix |

A stage is entered only after its previous workload envelope meets latency, error, correctness and recovery criteria. Add partitioning or read replicas only when measured query and write patterns justify them. Avoid giving every browser a database connection. PostgreSQL pools need a host-wide connection budget across all replicas and workers.

## AI and execution capacity

Use durable admission queues, per-tenant concurrency/token budgets, queue deadlines, cancellation and backpressure. Size local inference from measured tokens/second, prompt/context length, output length, model memory and review multiplier. Size sandbox workers from measured case runtime and resource envelopes. Approximate required busy inference slots as admitted jobs/second × measured service seconds/job, then add bounded utilization and redundancy headroom. No useful GPU count or monthly price can be asserted without that workload and hardware benchmark.

The current local-only model adapter does not become a remote GPU fleet by configuration. Secure distributed inference, workload identity, provider qualification and data-processing agreements need a separately reviewed adapter. Preserve model-digest checks and separate review/approval boundaries while scaling.

## Viral bursts, cost and recovery

Serve immutable public assets through a CDN; reserve private API paths from public caching. Apply quotas, request bounds, tenant fairness and queue admission before expensive work. Autoscaling must have an approved maximum, dependency limits and rollback/backpressure behavior. Database saturation, GPU queues, logging/egress costs and third-party quotas are practical blockers. Budget alerts are not spending caps.

One million 1MB initial downloads is approximately 1TB of transfer before repeat requests. Large-scale operation requires funded capacity, current regional pricing and workload-based estimates. Existing-host operation and future paid expansion are separate stages. See [performance qualification](performance-testing.md), [cost boundaries](cloud-costs.md) and [reliability](reliability.md).

References: [PostgreSQL connection resources](https://www.postgresql.org/docs/current/runtime-config-connection.html), [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
