# Operations

Build locally from the lockfile with the intended public origin. Keep versioned releases and content hashes. Validate the project server configuration before atomic activation, preserving unrelated applications.

## Website deployment

Build locally from the lockfile with the intended public origin. Keep versioned releases and content hashes. Validate the project server configuration before atomic activation, preserving unrelated applications.

## Backup and rollback

Retain an off-server release archive and verify extraction against the manifest. Keep a previous release for rollback. The future database phase adds encrypted off-host backups, retention and restore drills before valuable data is accepted.

## Recovery targets

Proposed initial application targets: RPO≤24h and RTO≤8h; later RPO≤15min/RTO≤1h after WAL/PITR and operational qualification. They remain targets until timed restoration evidence is published.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).
