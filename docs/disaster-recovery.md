# Backup and disaster recovery

## Current website

Recover from reviewed source, the lockfile, public configuration and retained
versioned build archives. A release archive includes the static output and its
server configuration. Extract it to a separate directory and compare every file
with the recorded SHA-256 manifest before treating it as recoverable.

Private access records and infrastructure inventory stay outside the public
repository. They must be backed up separately and protected. Losing the hosting
server must not also destroy the only copy of the release and recovery credentials.

## Future persistent service

Proposed startup goals are RPO≤24 hours and RTO≤8 hours. A later qualified operating
stage targets RPO≤15 minutes and RTO≤1 hour. They are targets until timed drills
establish feasibility for the actual workload.

RPO measures the acceptable loss window; RTO measures the target restoration time.
Define the incident start point, required restored functionality and data integrity
checks. A successful backup command is not proof of a usable restore.

PostgreSQL point-in-time recovery requires suitable base backups and retained WAL.
Private artifacts, configuration, encryption keys and provider access must also
have an explicit recovery owner. Encrypt off-host backups and separate their keys.

## Required drills

- Lost host: rebuild service and restore required records on clean infrastructure.
- Broken release: activate the retained prior version and verify real user flows.
- Failed migration: restore compatible state using the documented migration plan.
- Compromised credential: revoke, rotate and recover access without leaking old data.
- Unavailable provider: preserve task state and require approved fallback policy.

Record data point recovered, elapsed time, integrity checks and unresolved
dependencies. Repeat drills after meaningful schema/topology changes.

References: [PostgreSQL PITR](https://www.postgresql.org/docs/current/continuous-archiving.html),
[NIST RTO](https://csrc.nist.gov/glossary/term/recovery_time_objective).
