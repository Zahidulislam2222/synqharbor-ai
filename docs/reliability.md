# Reliability

Proposed website/core availability objective: 99% over rolling 30 days, corresponding to 7h 12m of time-based unavailability. Future multi-zone objective 99.9% corresponds to 43m 12s. These are objectives, not observed history or contractual promises.

## Initial operating objective

Proposed website/core availability objective: 99% over rolling 30 days, corresponding to 7h 12m of time-based unavailability. Future multi-zone objective 99.9% corresponds to 43m 12s. These are objectives, not observed history or contractual promises.

## Measurement policy

Separate website availability, authenticated API success/latency and asynchronous completion. Count eligible timeouts, 5xx and valid-workload 429s as failures. Define maintenance treatment, telemetry gaps and monitoring coverage explicitly.

## Response and recovery

Use public incident communication, error-budget-based prioritization, rollback procedures and postmortems. Backup success must be followed by a timed restore drill and application-level verification.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).
