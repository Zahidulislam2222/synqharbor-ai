# Backup and disaster recovery

## Scope and protection

Back up PostgreSQL, versioned source/static/config manifests, authorized repository state/receipts and the minimum private deployment configuration. Keep encryption keys and recovery credentials separate from backup archives. Model weights are reproducible from pinned manifests/digests; document whether retaining them improves recovery within the storage budget.

Use a consistent logical PostgreSQL dump or qualified physical/WAL backup process. Encrypt archives before off-host transfer, restrict permissions, define retention and monitor failed or stale backups. A local archive alone does not survive host loss. Keep at least one independently recoverable copy outside the server under operator control.

## Restore drill

1. Stop admissions or declare the recovery point and accepted-write risk.
2. Restore into a new isolated database with separate migration/runtime roles.
3. Verify schema head, table counts and deterministic row hashes, not only command exit status.
4. Check sessions, tenant isolation, source permissions, artifacts, approvals, run events and delivery receipts.
5. Reapply erasures/revocations and inspect uncertain external actions before retrying.
6. Restart services, exercise both workflows and verify public HTTPS behavior.
7. Record archive age, bytes, key recovery, elapsed restoration and final RPO/RTO.

Local and production qualification each restored all 21 ledger tables with exact row/hash equality from authenticated encrypted archives. The production archive is retained off-host with its key separately protected. Both completed workflow reports, artifact hashes and approval state were read back over HTTPS after the service restart. The timed controlled drill took 17.27 seconds from procedure setup through independent API/worker and HTTP readiness, with no accepted writes lost at its frozen recovery point. This isolated restore does not establish whole-host recovery, a continuously achieved RPO/RTO or scheduled backup coverage. Proposed initial RPO ≤24h/RTO ≤8h becomes an achieved statement only after measured operation. Future WAL/PITR and redundant infrastructure target RPO ≤15min/RTO ≤1h after qualification and approved funding.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
